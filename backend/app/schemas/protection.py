from pydantic import BaseModel, Field


class ProtectionConfig(BaseModel):
    require_auth: bool = True
    prompt_filtering: bool = True
    output_filtering: bool = True
    logging_enabled: bool = True
    anomaly_detection: bool = True
    rate_limit_enabled: bool = True


class ProtectionScoreResponse(BaseModel):
    model_id: int
    secure_mode_enabled: bool

    base_trust_score: float = Field(..., ge=0, le=100)
    protected_score: float = Field(..., ge=0, le=100)
    improvement_delta: float = Field(..., ge=0)

    active_controls: list[str] = Field(default_factory=list)
