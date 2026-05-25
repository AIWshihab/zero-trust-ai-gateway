from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class DeviceOut(BaseModel):
    id: int
    user_id: int
    device_fingerprint: str
    device_name: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    trust_score: float
    risk_level: str
    status: str
    login_count: int
    failed_attempts: int
    is_revoked: bool
    first_seen: datetime
    last_seen: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


class DeviceAdminOut(DeviceOut):
    user_agent_hash: Optional[str] = None
    ip_hash: Optional[str] = None


class DeviceTrustUpdate(BaseModel):
    status: str = Field(..., pattern="^(trusted|suspicious|revoked|new)$")
    trust_score: Optional[float] = Field(None, ge=0, le=100)
    reason: Optional[str] = None


class UserSessionOut(BaseModel):
    id: int
    user_id: int
    device_id: Optional[int] = None
    ip_hash: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_active_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    is_current: bool = False

    model_config = {"from_attributes": True}


class CurrentDeviceInfo(BaseModel):
    ip: str
    browser: str
    os: str
    user_agent: str
    fingerprint: str
    device_id: Optional[int] = None
    session_id: Optional[int] = None
    device: Optional[DeviceOut] = None
    session: Optional[UserSessionOut] = None


class DeviceEventOut(BaseModel):
    id: int
    event_type: str
    user_id: Optional[int] = None
    username_snapshot: Optional[str] = None
    device_id: Optional[int] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    severity: str
    risk_level: str
    source_module: Optional[str] = None
    explanation: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class UserModelCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    model_type: str = Field(..., pattern="^(openai|huggingface|local|custom_api)$")
    endpoint: Optional[str] = Field(None, max_length=500)
    provider_name: Optional[str] = Field(None, max_length=100)
    hf_model_id: Optional[str] = Field(None, max_length=255)
    auth_type: Optional[str] = Field(None, max_length=50)
    visibility: str = Field(default="private", pattern="^(private|shared)$")


class UserModelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    model_type: Optional[str] = Field(None, pattern="^(openai|huggingface|local|custom_api)$")
    endpoint: Optional[str] = Field(None, max_length=500)
    provider_name: Optional[str] = Field(None, max_length=100)
    hf_model_id: Optional[str] = Field(None, max_length=255)
    auth_type: Optional[str] = Field(None, max_length=50)
    visibility: Optional[str] = Field(None, pattern="^(private|shared)$")
    is_active: Optional[bool] = None
