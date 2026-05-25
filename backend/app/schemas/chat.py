from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    model_id: int | None = Field(default=None, gt=0)


class ChatSessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    model_id: int | None = Field(default=None, gt=0)


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    model_id: int | None = None
    decision: str | None = None
    prompt_risk_score: float | None = None
    security_score: float | None = None
    effective_risk: float | None = None
    blocked: bool | None = None
    gateway_trace: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionOut(BaseModel):
    id: int
    title: str
    model_id: int | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
