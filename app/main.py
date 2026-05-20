from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import APIError as GroqAPIError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.agent.graph import build_agent
from app.database import Base, engine, get_db, SessionLocal
from app.seed import seed_data
from app.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            seed_data(db)
    except OperationalError as exc:
        raise RuntimeError(
            "Database startup failed. Check DATABASE_URL in .env and confirm the "
            "Postgres user, password, and database are valid."
        ) from exc
    yield


app = FastAPI(title="AI-First CRM HCP Module", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "agent_configured": bool(settings.groq_api_key),
        "groq_model": settings.groq_model,
    }


@app.get("/api/hcps", response_model=list[schemas.HCPRead])
def read_hcps(db: Session = Depends(get_db)):
    return crud.list_hcps(db)


@app.get("/api/hcps/{hcp_id}", response_model=schemas.HCPDetail)
def read_hcp(hcp_id: int, db: Session = Depends(get_db)):
    hcp = crud.get_hcp(db, hcp_id)
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp


@app.get("/api/interactions", response_model=list[schemas.InteractionRead])
def read_interactions(db: Session = Depends(get_db)):
    return crud.list_interactions(db)


@app.post("/api/interactions", response_model=schemas.InteractionRead)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    return crud.create_interaction(db, payload)


@app.put("/api/interactions/{interaction_id}", response_model=schemas.InteractionRead)
def update_interaction(
    interaction_id: int, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)
):
    interaction = crud.update_interaction(db, interaction_id, payload)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@app.post("/api/agent/run", response_model=schemas.AgentResponse)
async def run_agent(payload: schemas.AgentRequest):
    try:
        agent = build_agent()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": payload.message}]})
    except GroqAPIError as exc:
        provider_message = getattr(exc, "body", {}).get("error", {}).get("message")
        detail = provider_message or f"Groq request failed while using model '{settings.groq_model}'."
        raise HTTPException(status_code=502, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Agent execution failed before a response was produced.",
        ) from exc

    messages = result["messages"]
    reply = ""
    tool_messages: list[str] = []

    for message in messages:
        msg_type = getattr(message, "type", "")
        content = getattr(message, "content", "")
        if msg_type == "tool":
            tool_messages.append(str(content))
        elif msg_type == "ai" and content:
            reply = str(content)

    return schemas.AgentResponse(reply=reply, tool_messages=tool_messages)
