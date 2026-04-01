from sqlalchemy import Boolean, Column, Float, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.schemas import ModelType, SensitivityLevel, RiskLevel


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