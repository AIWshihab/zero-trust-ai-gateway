from typing import Optional

from pydantic import BaseModel, Field


class ComparisonReportResponse(BaseModel):
    model_id: int
    model_name: str
    provider_name: Optional[str] = None

    base_trust_score: float = Field(..., ge=0, le=100)
    protected_score: float = Field(..., ge=0, le=100)
    improvement_delta: float = Field(..., ge=0)

    secure_mode_enabled: bool
    total_requests: int
    blocked_count: int
    challenged_count: int
    allowed_count: int
    blocked_requests: int
    challenged_requests: int
    allowed_requests: int
    avg_prompt_risk_score: float = Field(..., ge=0, le=1)
    avg_output_risk_score: float = Field(..., ge=0, le=100)
    avg_latency_ms: float = Field(..., ge=0)

    latest_findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
