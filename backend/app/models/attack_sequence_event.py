from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class AttackSequenceEvent(Base):
    __tablename__ = "attack_sequence_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    model_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("models.id"), nullable=True, index=True)

    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    attack_stage: Mapped[str] = mapped_column(String, nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String, nullable=False, index=True)

    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    security_score: Mapped[float] = mapped_column(Float, nullable=False)
    sequence_severity: Mapped[float] = mapped_column(Float, nullable=False)
    repeated_pattern_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cross_model_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
