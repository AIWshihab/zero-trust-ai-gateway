from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.enums import RequestDecision


class DetectRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4096)
    user_id: Optional[int] = Field(None, gt=0)
    model_id: Optional[int] = Field(None, gt=0)


class DetectResponse(BaseModel):
    prompt_risk_score: float = Field(..., ge=0, le=1)
    flags: list[str] = Field(default_factory=list)

    decision: RequestDecision
    reason: str
    enforcement_profile: dict = Field(default_factory=dict)
