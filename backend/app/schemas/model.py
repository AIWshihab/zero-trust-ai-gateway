from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.enums import ModelType, RiskLevel, ScanStatus, SensitivityLevel


class ModelBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    model_type: ModelType
    sensitivity_level: SensitivityLevel
    risk_level: RiskLevel

    endpoint: Optional[str] = Field(None, max_length=500)
    source_url: Optional[str] = Field(None, max_length=500)
    provider_name: Optional[str] = Field(None, max_length=100)
    hf_model_id: Optional[str] = Field(None, max_length=255)
    auth_type: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class ModelCreate(ModelBase):
    pass


class ModelOut(ModelBase):
    id: int
    created_at: datetime
    base_trust_score: Optional[float] = Field(None, ge=0, le=100)
    protected_score: Optional[float] = Field(None, ge=0, le=100)
    secure_mode_enabled: bool = False
    scan_status: Optional[ScanStatus] = None
    last_scan_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ModelRiskInfoResponse(BaseModel):
    model_id: int
    name: str
    risk_level: RiskLevel
    sensitivity_level: SensitivityLevel
    risk_score: float = Field(..., ge=0, le=1)
    sensitivity_score: float = Field(..., ge=0, le=1)
