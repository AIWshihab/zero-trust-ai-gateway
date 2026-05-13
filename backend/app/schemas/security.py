from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import RequestDecision


CoverageLevel = Literal["strong", "moderate", "partial", "planned"]
ControlStatus = Literal["active", "roadmap", "planned", "deprecated"]
RuleTarget = Literal["prompt", "output"]
RuleMatchType = Literal["keyword", "regex"]
RuleSeverity = Literal["low", "medium", "high", "critical"]


class SecurityControlBase(BaseModel):
    control_id: str = Field(..., min_length=2, max_length=40)
    name: str = Field(..., min_length=2, max_length=160)
    description: str | None = Field(None, max_length=1200)
    framework: str = Field("OWASP Top 10 for LLM Applications 2025", max_length=160)
    coverage: CoverageLevel = "planned"
    status: ControlStatus = "active"
    control_family: str | None = Field(None, max_length=100)
    mapped_capabilities: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    enabled: bool = True

    @field_validator("control_id")
    @classmethod
    def normalize_control_id(cls, value: str) -> str:
        return value.strip().upper()


class SecurityControlCreate(SecurityControlBase):
    pass


class SecurityControlUpdate(BaseModel):
    control_id: str | None = Field(None, min_length=2, max_length=40)
    name: str | None = Field(None, min_length=2, max_length=160)
    description: str | None = Field(None, max_length=1200)
    framework: str | None = Field(None, max_length=160)
    coverage: CoverageLevel | None = None
    status: ControlStatus | None = None
    control_family: str | None = Field(None, max_length=100)
    mapped_capabilities: list[str] | None = None
    recommended_actions: list[str] | None = None
    enabled: bool | None = None

    @field_validator("control_id")
    @classmethod
    def normalize_control_id(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None


class SecurityControlOut(SecurityControlBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DetectionRuleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    description: str | None = Field(None, max_length=1200)
    target: RuleTarget
    match_type: RuleMatchType
    pattern: str = Field(..., min_length=1, max_length=1000)
    severity: RuleSeverity = "medium"
    decision: RequestDecision = RequestDecision.CHALLENGE
    risk_delta: float = Field(0.15, ge=0, le=1)
    enabled: bool = True
    metadata_json: dict[str, Any] | None = Field(default_factory=dict)


class DetectionRuleCreate(DetectionRuleBase):
    pass


class DetectionRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=160)
    description: str | None = Field(None, max_length=1200)
    target: RuleTarget | None = None
    match_type: RuleMatchType | None = None
    pattern: str | None = Field(None, min_length=1, max_length=1000)
    severity: RuleSeverity | None = None
    decision: RequestDecision | None = None
    risk_delta: float | None = Field(None, ge=0, le=1)
    enabled: bool | None = None
    metadata_json: dict[str, Any] | None = None


class DetectionRuleOut(DetectionRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
