from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.enums import RequestDecision


class InferenceRequest(BaseModel):
    model_id: int = Field(..., gt=0)
    prompt: str = Field(..., min_length=1, max_length=4096)
    parameters: dict[str, Any] = Field(default_factory=dict)


class InferenceResponse(BaseModel):
    model_id: int
    output: Optional[str] = None

    decision: RequestDecision
    security_score: float = Field(..., ge=0, le=1)

    blocked: bool
    reason: Optional[str] = None
    latency_ms: Optional[float] = Field(None, ge=0)


class SafeInferenceResponse(BaseModel):
    model_id: int
    output: Optional[str] = None

    decision: RequestDecision
    security_score: float = Field(0.0, ge=0, le=1)
    prompt_risk_score: float = Field(..., ge=0, le=1)
    output_risk_score: float = Field(..., ge=0, le=100)

    blocked: bool
    reason: Optional[str] = None
    latency_ms: Optional[float] = Field(None, ge=0)
    secure_mode_enabled: bool = False
    enforcement_profile: dict[str, Any] = Field(default_factory=dict)
