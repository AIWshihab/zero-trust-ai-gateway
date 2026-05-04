from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.enums import RequestDecision


class GatewayInterceptRequest(BaseModel):
    model_id: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    prompt: Optional[str] = Field(default=None, min_length=1, max_length=4096)
    external_user_id: Optional[str] = None
    client_id: Optional[str] = None
    policy_context: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)


class GatewayInterceptResponse(BaseModel):
    decision: RequestDecision
    output: Optional[str] = None
    reason: Optional[str] = None
    effective_risk: float = Field(0.0, ge=0, le=1)
    trace_id: str
    forwarded: bool
    factors: dict[str, Any] = Field(default_factory=dict)
    explanation: Optional[str] = None
    decision_trace: dict[str, Any] = Field(default_factory=dict)


class FirewallProxyResponse(GatewayInterceptResponse):
    client_id: str
    rate: dict[str, Any] = Field(default_factory=dict)


class FirewallClientCreate(BaseModel):
    client_id: str = Field(..., min_length=2, max_length=80)
    name: str = Field(..., min_length=1, max_length=160)
    api_key: Optional[str] = Field(default=None, min_length=8)
    rate_limit: int = Field(default=60, ge=1, le=10000)
    rate_window_seconds: int = Field(default=60, ge=1, le=86400)
    trust_score: float = Field(default=0.8, ge=0, le=1)
    require_signature: bool = False
    hmac_secret: Optional[str] = None
    is_active: bool = True


class FirewallClientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    api_key: Optional[str] = Field(default=None, min_length=8)
    rate_limit: Optional[int] = Field(default=None, ge=1, le=10000)
    rate_window_seconds: Optional[int] = Field(default=None, ge=1, le=86400)
    trust_score: Optional[float] = Field(default=None, ge=0, le=1)
    require_signature: Optional[bool] = None
    hmac_secret: Optional[str] = None
    is_active: Optional[bool] = None


class FirewallClientOut(BaseModel):
    id: int
    client_id: str
    name: str
    rate_limit: int
    rate_window_seconds: int
    trust_score: float
    require_signature: bool
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    api_key: Optional[str] = None


class OpenAIChatCompletionRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]] = Field(..., min_length=1)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False


class OpenAIChatCompletionMessage(BaseModel):
    role: str
    content: str


class OpenAIChatCompletionChoice(BaseModel):
    message: OpenAIChatCompletionMessage
    finish_reason: str = "stop"


class OpenAIChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    choices: list[OpenAIChatCompletionChoice]
