from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("models.id"),
        nullable=False,
        index=True,
    )

    prompt_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)

    security_score: Mapped[float] = mapped_column(Float, nullable=False)
    prompt_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    output_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    decision: Mapped[str] = mapped_column(String, nullable=False, index=True)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    secure_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Explainability snapshots persisted at decision time.
    decision_input_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    decision_trace: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
