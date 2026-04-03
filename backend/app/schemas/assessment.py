from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.enums import ModelType, ScanStatus


class ModelScanRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    model_type: ModelType
    provider_name: Optional[str] = Field(None, max_length=100)
    source_url: Optional[str] = Field(None, max_length=500)
    hf_model_id: Optional[str] = Field(None, max_length=255)
    endpoint: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=500)


class TrustBreakdownSchema(BaseModel):
    source_reputation: float = Field(..., ge=0, le=100)
    metadata_completeness: float = Field(..., ge=0, le=100)
    endpoint_security: float = Field(..., ge=0, le=100)
    behavioral_safety: float = Field(..., ge=0, le=100)
    infrastructure_posture: float = Field(..., ge=0, le=100)


class ModelScanResponse(BaseModel):
    model_id: int
    model_name: str
    model_type: ModelType
    provider_name: Optional[str] = None

    base_trust_score: float = Field(..., ge=0, le=100)
    breakdown: TrustBreakdownSchema

    findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    secure_mode_enabled: bool = False
    scan_status: ScanStatus

    raw_inputs: dict[str, Any] = Field(default_factory=dict)
