from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from app.agent.tools import TOOLS
from app.config import settings


SYSTEM_PROMPT = """
You are an AI-first CRM copilot for life sciences field representatives.

Your job is to help users work on the HCP interaction logging workflow.
Always prefer using tools when the user asks for concrete CRM actions or data retrieval.
When logging interactions:
- capture the doctor, channel, objective, summary, sentiment, products discussed, and follow-up when available
- keep the final answer concise and business-ready
- if a required detail is missing, ask one clear follow-up question
"""


def build_agent():
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Set it in .env or the process environment "
            "before calling /api/agent/run."
        )

    model = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.1,
    )
    return create_react_agent(model, TOOLS, prompt=SYSTEM_PROMPT)
