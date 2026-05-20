from datetime import date, datetime

from pydantic import BaseModel, Field


class HCPBase(BaseModel):
    full_name: str
    specialty: str
    organization: str
    city: str
    tier: str
    preferred_channel: str
    prescribing_focus: str
    notes: str = ""


class HCPRead(HCPBase):
    id: int

    model_config = {"from_attributes": True}


class InteractionBase(BaseModel):
    hcp_id: int
    interaction_date: date
    channel: str
    title: str
    objective: str
    summary: str
    sentiment: str = "neutral"
    products_discussed: list[str] = Field(default_factory=list)
    follow_up_date: date | None = None
    next_action: str = ""


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_date: date | None = None
    channel: str | None = None
    title: str | None = None
    objective: str | None = None
    summary: str | None = None
    sentiment: str | None = None
    products_discussed: list[str] | None = None
    follow_up_date: date | None = None
    next_action: str | None = None


class InteractionRead(InteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HCPDetail(HCPRead):
    interactions: list[InteractionRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    reply: str
    tool_messages: list[str] = Field(default_factory=list)
