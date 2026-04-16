from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class UserTrustEvent(Base):
    __tablename__ = "user_trust_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    username_snapshot: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)

    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_value: Mapped[float] = mapped_column(Float, nullable=False)

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    context_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
