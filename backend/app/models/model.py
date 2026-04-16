from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SAEnum, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base
from app.schemas import ModelType, RiskLevel, SensitivityLevel


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    model_type = Column(SAEnum(ModelType, name="modeltype"), nullable=True)
    sensitivity_level = Column(SAEnum(SensitivityLevel, name="sensitivitylevel"), nullable=True)
    risk_level = Column(SAEnum(RiskLevel, name="risklevel"), nullable=True)

    endpoint = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    source_url = Column(String, nullable=True)
    provider_name = Column(String, nullable=True)
    hf_model_id = Column(String, nullable=True)
    auth_type = Column(String, nullable=True)

    has_model_card = Column(Boolean, default=False)
    supports_https = Column(Boolean, default=False)
    requires_auth = Column(Boolean, default=False)

    base_trust_score = Column(Float, nullable=True)
    protected_score = Column(Float, nullable=True)

    # Model-risk posture foundation (all 0-100 scale except where noted)
    base_risk_score = Column(Float, nullable=True)
    secured_risk_score = Column(Float, nullable=True)
    risk_reduction_pct = Column(Float, nullable=True)

    # Structured explainability snapshots from posture evaluation.
    posture_factors = Column(JSON, nullable=True)
    posture_explanations = Column(JSON, nullable=True)

    posture_assessed_at = Column(DateTime(timezone=True), nullable=True)
    posture_expires_at = Column(DateTime(timezone=True), nullable=True)
    last_reassessed_at = Column(DateTime(timezone=True), nullable=True)

    # Freshness-oriented scan metadata.
    scan_valid_until = Column(DateTime(timezone=True), nullable=True)
    scan_freshness_days = Column(Integer, nullable=True)

    secure_mode_enabled = Column(Boolean, default=False)
    scan_status = Column(String, nullable=True)
    scan_summary_json = Column(Text, nullable=True)

    last_scan_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
