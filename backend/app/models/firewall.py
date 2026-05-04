from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class FirewallClient(Base):
    __tablename__ = "firewall_clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hmac_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    require_signature: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rate_limit: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    rate_window_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
