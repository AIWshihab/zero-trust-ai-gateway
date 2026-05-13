from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.enums import RequestDecision


class RequestLog(BaseModel):
    id: int
    user_id: Optional[int]
    model_id: Optional[int]

    prompt_hash: str

    security_score: float = Field(..., ge=0, le=1)
    decision: RequestDecision

    reason: Optional[str] = None
    decision_input_snapshot: Optional[dict[str, Any]] = None
    decision_trace: Optional[dict[str, Any]] = None

    timestamp: datetime
    latency_ms: float = Field(..., ge=0)

    model_config = {"from_attributes": True}


class MetricsSummary(BaseModel):
    total_requests: int
    blocked_requests: int
    challenged_requests: int
    allowed_requests: int

    avg_security_score: float
    avg_latency_ms: float


class ValueChangeEvent(BaseModel):
    event_type: str
    previous_value: Optional[float] = None
    new_value: Optional[float] = None
    reason: str
    timestamp: datetime
    context_json: dict[str, Any] = Field(default_factory=dict)


class UserTrustEventResponse(ValueChangeEvent):
    id: int
    user_id: int
    username_snapshot: str


class ModelPostureEventResponse(ValueChangeEvent):
    id: int
    model_id: int
    model_name_snapshot: Optional[str] = None
    metric_name: str
