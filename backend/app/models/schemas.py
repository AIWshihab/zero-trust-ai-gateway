from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, EmailStr, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class ModelType(str, Enum):
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM_API = "custom_api"


class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequestDecision(str, Enum):
    ALLOW = "allow"
    CHALLENGE = "challenge"
    BLOCK = "block"


# ─── Auth Schemas ─────────────────────────────────────────────────────────────


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)


# ─── User Schemas ─────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    trust_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Model Registry Schemas ───────────────────────────────────────────────────


class ModelBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    model_type: ModelType
    sensitivity_level: SensitivityLevel
    risk_level: RiskLevel

    endpoint: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class ModelCreate(ModelBase):
    pass


class ModelOut(ModelBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Inference Request/Response ───────────────────────────────────────────────


class InferenceRequest(BaseModel):
    model_id: int = Field(..., gt=0)
    prompt: str = Field(..., min_length=1, max_length=4096)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class InferenceResponse(BaseModel):
    model_id: int
    output: Optional[str] = None

    decision: RequestDecision
    security_score: float = Field(..., ge=0, le=1)

    blocked: bool
    reason: Optional[str] = None
    latency_ms: Optional[float] = Field(None, ge=0)


# ─── Detection / Policy Schemas ───────────────────────────────────────────────


class DetectRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4096)
    user_id: Optional[int] = Field(None, gt=0)
    model_id: Optional[int] = Field(None, gt=0)


class DetectResponse(BaseModel):
    prompt_risk_score: float = Field(..., ge=0, le=1)
    flags: List[str] = Field(default_factory=list)

    decision: RequestDecision
    reason: str


# ─── Monitoring / Log Schemas ─────────────────────────────────────────────────


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

# ─── Assessment / Trust Scan Schemas ──────────────────────────────────────────


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

    findings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

    secure_mode_enabled: bool = False
    scan_status: str

    raw_inputs: Dict[str, Any] = Field(default_factory=dict)


# ─── Protection Schemas ───────────────────────────────────────────────────────


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

    active_controls: List[str] = Field(default_factory=list)


# ─── Safe Usage Extended Schemas ──────────────────────────────────────────────


class SafeInferenceResponse(BaseModel):
    model_id: int
    output: Optional[str] = None

    decision: RequestDecision
    prompt_risk_score: float = Field(..., ge=0, le=1)
    output_risk_score: float = Field(..., ge=0, le=100)

    blocked: bool
    reason: Optional[str] = None
    latency_ms: Optional[float] = Field(None, ge=0)
    secure_mode_enabled: bool = False

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

    active_controls: List[str] = Field(default_factory=list)

class ComparisonReportResponse(BaseModel):
    model_id: int
    model_name: str
    provider_name: Optional[str] = None

    base_trust_score: float = Field(..., ge=0, le=100)
    protected_score: float = Field(..., ge=0, le=100)
    improvement_delta: float = Field(..., ge=0)

    secure_mode_enabled: bool
    total_requests: int
    blocked_requests: int
    challenged_requests: int
    allowed_requests: int
    avg_prompt_risk_score: float = Field(..., ge=0, le=1)
    avg_output_risk_score: float = Field(..., ge=0, le=100)
    avg_latency_ms: float = Field(..., ge=0)

    latest_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)