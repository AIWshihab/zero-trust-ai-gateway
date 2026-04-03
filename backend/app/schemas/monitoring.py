from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.enums import RequestDecision


class RequestLog(BaseModel):
    id: int
    user_id: Optional[int]
    model_id: Optional[int]

    prompt_hash: str

    security_score: float = Field(..., ge=0, le=1)
    decision: RequestDecision

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
