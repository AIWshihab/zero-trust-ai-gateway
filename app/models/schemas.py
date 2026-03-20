from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


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


# ─── Auth Schemas ──────────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []


# ─── User Schemas ──────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    trust_score: float = 1.0
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Model Registry Schemas ────────────────────────────────────────────────────

class ModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: ModelType
    sensitivity_level: SensitivityLevel
    risk_level: RiskLevel
    endpoint: Optional[str] = None
    is_active: bool = True

class ModelCreate(ModelBase):
    pass

class ModelOut(ModelBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Inference Request/Response ────────────────────────────────────────────────

class InferenceRequest(BaseModel):
    model_id: int
    prompt: str = Field(..., min_length=1, max_length=4096)
    parameters: Optional[dict] = {}

class InferenceResponse(BaseModel):
    model_id: int
    output: Optional[str] = None
    decision: RequestDecision
    security_score: float
    blocked: bool
    reason: Optional[str] = None
    latency_ms: Optional[float] = None


# ─── Detection / Policy Schemas ────────────────────────────────────────────────

class DetectRequest(BaseModel):
    prompt: str
    user_id: Optional[int] = None
    model_id: Optional[int] = None

class DetectResponse(BaseModel):
    prompt_risk_score: float
    flags: List[str]
    decision: RequestDecision
    reason: str


# ─── Monitoring / Log Schemas ──────────────────────────────────────────────────

class RequestLog(BaseModel):
    id: int
    user_id: Optional[int]
    model_id: Optional[int]
    prompt_hash: str
    security_score: float
    decision: RequestDecision
    timestamp: datetime
    latency_ms: float

    class Config:
        from_attributes = True

class MetricsSummary(BaseModel):
    total_requests: int
    blocked_requests: int
    challenged_requests: int
    allowed_requests: int
    avg_security_score: float
    avg_latency_ms: float
