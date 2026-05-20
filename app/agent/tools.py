import json
from datetime import date
from typing import Any

from langchain_core.tools import tool

from app import crud, schemas
from app.database import SessionLocal


def _json(data: Any) -> str:
    return json.dumps(data, default=str, indent=2)


def _normalize_products_discussed(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


@tool
def list_hcps() -> str:
    """List all available healthcare professionals with lightweight profile details."""
    with SessionLocal() as db:
        hcps = crud.list_hcps(db)
        payload = [
            {
                "id": hcp.id,
                "full_name": hcp.full_name,
                "specialty": hcp.specialty,
                "organization": hcp.organization,
                "tier": hcp.tier,
                "preferred_channel": hcp.preferred_channel,
            }
            for hcp in hcps
        ]
        return _json(payload)


@tool
def get_hcp_snapshot(hcp_id: int) -> str:
    """Fetch a detailed HCP profile including prior interactions for context."""
    with SessionLocal() as db:
        hcp = crud.get_hcp(db, hcp_id)
        if not hcp:
            return f"HCP {hcp_id} was not found."

        payload = {
            "id": hcp.id,
            "full_name": hcp.full_name,
            "specialty": hcp.specialty,
            "organization": hcp.organization,
            "city": hcp.city,
            "tier": hcp.tier,
            "preferred_channel": hcp.preferred_channel,
            "prescribing_focus": hcp.prescribing_focus,
            "notes": hcp.notes,
            "recent_interactions": [
                {
                    "id": item.id,
                    "date": item.interaction_date,
                    "channel": item.channel,
                    "title": item.title,
                    "summary": item.summary,
                    "sentiment": item.sentiment,
                    "next_action": item.next_action,
                }
                for item in hcp.interactions[:5]
            ],
        }
        return _json(payload)


@tool
def log_interaction(
    hcp_id: int,
    channel: str,
    title: str,
    objective: str,
    summary: str,
    sentiment: str = "neutral",
    products_discussed: list[str] | str | None = None,
    interaction_date: str | None = None,
    follow_up_date: str | None = None,
    next_action: str = "",
) -> str:
    """Log a new HCP interaction entry into the CRM."""
    with SessionLocal() as db:
        payload = schemas.InteractionCreate(
            hcp_id=hcp_id,
            interaction_date=date.fromisoformat(interaction_date) if interaction_date else date.today(),
            channel=channel,
            title=title,
            objective=objective,
            summary=summary,
            sentiment=sentiment,
            products_discussed=_normalize_products_discussed(products_discussed),
            follow_up_date=date.fromisoformat(follow_up_date) if follow_up_date else None,
            next_action=next_action,
        )
        interaction = crud.create_interaction(db, payload)
        return _json(
            {
                "status": "created",
                "interaction_id": interaction.id,
                "hcp_id": interaction.hcp_id,
                "title": interaction.title,
                "summary": interaction.summary,
            }
        )


@tool
def edit_interaction(
    interaction_id: int,
    summary: str | None = None,
    next_action: str | None = None,
    sentiment: str | None = None,
    follow_up_date: str | None = None,
    channel: str | None = None,
    title: str | None = None,
    objective: str | None = None,
    products_discussed: list[str] | str | None = None,
) -> str:
    """Edit an existing interaction when a rep wants to correct or enrich the record."""
    with SessionLocal() as db:
        payload = schemas.InteractionUpdate(
            summary=summary,
            next_action=next_action,
            sentiment=sentiment,
            follow_up_date=date.fromisoformat(follow_up_date) if follow_up_date else None,
            channel=channel,
            title=title,
            objective=objective,
            products_discussed=_normalize_products_discussed(products_discussed)
            if products_discussed is not None
            else None,
        )
        interaction = crud.update_interaction(db, interaction_id, payload)
        if not interaction:
            return f"Interaction {interaction_id} was not found."

        return _json(
            {
                "status": "updated",
                "interaction_id": interaction.id,
                "summary": interaction.summary,
                "sentiment": interaction.sentiment,
                "next_action": interaction.next_action,
            }
        )


@tool
def recommend_next_best_action(hcp_id: int, business_goal: str) -> str:
    """Recommend the next best field action for an HCP based on prior context and intent."""
    with SessionLocal() as db:
        hcp = crud.get_hcp(db, hcp_id)
        if not hcp:
            return f"HCP {hcp_id} was not found."

        last_note = hcp.interactions[0].summary if hcp.interactions else "No prior interactions"
        recommendation = {
            "hcp_id": hcp.id,
            "hcp_name": hcp.full_name,
            "business_goal": business_goal,
            "suggested_action": (
                f"Use {hcp.preferred_channel} to follow up on {business_goal.lower()} and connect it to "
                f"{hcp.prescribing_focus.lower()}."
            ),
            "why": f"Latest context: {last_note}",
        }
        return _json(recommendation)


@tool
def draft_follow_up(hcp_id: int, purpose: str) -> str:
    """Draft a short tailored follow-up note for the HCP after an interaction."""
    with SessionLocal() as db:
        hcp = crud.get_hcp(db, hcp_id)
        if not hcp:
            return f"HCP {hcp_id} was not found."

        message = (
            f"Dear {hcp.full_name},\n\n"
            f"Thank you for your time today. As discussed, I am sharing a concise follow-up on {purpose.lower()} "
            f"relevant to your work in {hcp.specialty.lower()} at {hcp.organization}. "
            f"I can also arrange a focused discussion aligned to {hcp.prescribing_focus.lower()}.\n\n"
            "Regards,\nField Representative"
        )
        return _json({"hcp_id": hcp.id, "draft": message})


TOOLS = [
    list_hcps,
    get_hcp_snapshot,
    log_interaction,
    edit_interaction,
    recommend_next_best_action,
    draft_follow_up,
]
