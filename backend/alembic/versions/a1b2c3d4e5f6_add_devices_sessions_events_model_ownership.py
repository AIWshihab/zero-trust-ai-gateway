"""add devices sessions device_events model ownership

Revision ID: a1b2c3d4e5f6
Revises: b7f4c2a19d03
Create Date: 2026-05-13 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


def _has_table(inspector: Inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def _has_column(inspector: Inspector, table: str, column: str) -> bool:
    if not _has_table(inspector, table):
        return False
    return any(c["name"] == column for c in inspector.get_columns(table))


def _has_index(inspector: Inspector, table: str, index: str) -> bool:
    if not _has_table(inspector, table):
        return False
    return any(ix["name"] == index for ix in inspector.get_indexes(table))


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "b7f4c2a19d03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = Inspector.from_engine(op.get_bind())
    dialect = op.get_bind().dialect.name

    # ── 1. Add ownership columns to models table ──────────────────────────────
    # Note: no ForeignKey in ADD COLUMN — SQLite doesn't support it via ALTER.
    # The FK relationship is enforced at the ORM layer instead.
    if not _has_column(inspector, "models", "owner_user_id"):
        op.add_column(
            "models",
            sa.Column("owner_user_id", sa.Integer(), nullable=True),
        )
    if not _has_column(inspector, "models", "visibility"):
        op.add_column(
            "models",
            sa.Column("visibility", sa.String(16), nullable=False, server_default="global"),
        )
    if not _has_index(inspector, "models", "ix_models_owner_user_id"):
        op.create_index("ix_models_owner_user_id", "models", ["owner_user_id"])

    # ── 2. Create devices table ───────────────────────────────────────────────
    if not _has_table(inspector, "devices"):
        op.create_table(
            "devices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("device_fingerprint", sa.String(128), nullable=False),
            sa.Column("device_name", sa.String(255), nullable=True),
            sa.Column("browser", sa.String(128), nullable=True),
            sa.Column("os", sa.String(128), nullable=True),
            sa.Column("user_agent_hash", sa.String(64), nullable=True),
            sa.Column("ip_hash", sa.String(64), nullable=True),
            sa.Column("trust_score", sa.Float(), nullable=False, server_default="70"),
            sa.Column("risk_level", sa.String(16), nullable=False, server_default="medium"),
            sa.Column("status", sa.String(16), nullable=False, server_default="new"),
            sa.Column("login_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_devices_id", "devices", ["id"])
        op.create_index("ix_devices_user_id", "devices", ["user_id"])
        op.create_index("ix_devices_device_fingerprint", "devices", ["device_fingerprint"])
        op.create_index("ix_devices_status", "devices", ["status"])
        op.create_index("ix_devices_last_seen", "devices", ["last_seen"])

    # ── 3. Create user_sessions table ─────────────────────────────────────────
    if not _has_table(inspector, "user_sessions"):
        op.create_table(
            "user_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_token_hash", sa.String(128), nullable=False),
            sa.Column("ip_hash", sa.String(64), nullable=True),
            sa.Column("user_agent", sa.String(512), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_user_sessions_id", "user_sessions", ["id"])
        op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
        op.create_index("ix_user_sessions_device_id", "user_sessions", ["device_id"])
        op.create_index("ix_user_sessions_is_active", "user_sessions", ["is_active"])
        op.create_index("ix_user_sessions_session_token_hash", "user_sessions", ["session_token_hash"])
        op.create_index("ix_user_sessions_created_at", "user_sessions", ["created_at"])

    # ── 4. Create device_events table ─────────────────────────────────────────
    if not _has_table(inspector, "device_events"):
        op.create_table(
            "device_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("event_type", sa.String(64), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("username_snapshot", sa.String(128), nullable=True),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_id", sa.Integer(), sa.ForeignKey("user_sessions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("browser", sa.String(128), nullable=True),
            sa.Column("os", sa.String(128), nullable=True),
            sa.Column("ip_hash", sa.String(64), nullable=True),
            sa.Column("severity", sa.String(16), nullable=False, server_default="info"),
            sa.Column("risk_level", sa.String(16), nullable=False, server_default="low"),
            sa.Column("source_module", sa.String(64), nullable=True),
            sa.Column("explanation", sa.Text(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_device_events_id", "device_events", ["id"])
        op.create_index("ix_device_events_user_id", "device_events", ["user_id"])
        op.create_index("ix_device_events_device_id", "device_events", ["device_id"])
        op.create_index("ix_device_events_event_type", "device_events", ["event_type"])
        op.create_index("ix_device_events_severity", "device_events", ["severity"])
        op.create_index("ix_device_events_risk_level", "device_events", ["risk_level"])
        op.create_index("ix_device_events_timestamp", "device_events", ["timestamp"])


def downgrade() -> None:
    inspector = Inspector.from_engine(op.get_bind())

    for idx in ["ix_device_events_timestamp", "ix_device_events_risk_level",
                "ix_device_events_severity", "ix_device_events_event_type",
                "ix_device_events_device_id", "ix_device_events_user_id", "ix_device_events_id"]:
        if _has_index(inspector, "device_events", idx):
            op.drop_index(idx, table_name="device_events")
    if _has_table(inspector, "device_events"):
        op.drop_table("device_events")

    for idx in ["ix_user_sessions_created_at", "ix_user_sessions_session_token_hash",
                "ix_user_sessions_is_active", "ix_user_sessions_device_id",
                "ix_user_sessions_user_id", "ix_user_sessions_id"]:
        if _has_index(inspector, "user_sessions", idx):
            op.drop_index(idx, table_name="user_sessions")
    if _has_table(inspector, "user_sessions"):
        op.drop_table("user_sessions")

    for idx in ["ix_devices_last_seen", "ix_devices_status", "ix_devices_device_fingerprint",
                "ix_devices_user_id", "ix_devices_id"]:
        if _has_index(inspector, "devices", idx):
            op.drop_index(idx, table_name="devices")
    if _has_table(inspector, "devices"):
        op.drop_table("devices")

    if _has_index(inspector, "models", "ix_models_owner_user_id"):
        op.drop_index("ix_models_owner_user_id", table_name="models")
    if _has_column(inspector, "models", "visibility"):
        op.drop_column("models", "visibility")
    if _has_column(inspector, "models", "owner_user_id"):
        op.drop_column("models", "owner_user_id")
