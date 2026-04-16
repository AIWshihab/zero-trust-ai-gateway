from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ModelPostureEvent(Base):
    __tablename__ = "model_posture_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey("models.id"), nullable=False, index=True)

    model_name_snapshot: Mapped[str | None] = mapped_column(String, nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String, nullable=False, index=True)

    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    context_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
