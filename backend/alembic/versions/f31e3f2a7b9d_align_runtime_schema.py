"""align runtime schema

Revision ID: f31e3f2a7b9d
Revises: c1dd4cadc258
Create Date: 2026-04-03 22:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f31e3f2a7b9d"
down_revision: Union[str, Sequence[str], None] = "c1dd4cadc258"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _add_column_if_missing(
    inspector,
    table_name: str,
    column: sa.Column,
) -> None:
    if not _has_column(inspector, table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _add_column_if_missing(
        inspector,
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    if _has_column(inspector, "users", "is_admin"):
        op.alter_column("users", "is_admin", server_default=None)

    if not _has_table(inspector, "request_logs"):
        op.create_table(
            "request_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("model_id", sa.Integer(), nullable=False),
            sa.Column("prompt_hash", sa.String(), nullable=False),
            sa.Column("security_score", sa.Float(), nullable=False),
            sa.Column("prompt_risk_score", sa.Float(), nullable=True),
            sa.Column("output_risk_score", sa.Float(), nullable=True),
            sa.Column("decision", sa.String(), nullable=False),
            sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("secure_mode_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("latency_ms", sa.Float(), nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["model_id"], ["models.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_request_logs_id"), "request_logs", ["id"], unique=False)
        op.create_index(op.f("ix_request_logs_model_id"), "request_logs", ["model_id"], unique=False)
        op.create_index(op.f("ix_request_logs_prompt_hash"), "request_logs", ["prompt_hash"], unique=False)
        op.create_index(op.f("ix_request_logs_decision"), "request_logs", ["decision"], unique=False)
        op.create_index(op.f("ix_request_logs_timestamp"), "request_logs", ["timestamp"], unique=False)

    model_columns = [
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("provider_name", sa.String(), nullable=True),
        sa.Column("hf_model_id", sa.String(), nullable=True),
        sa.Column("auth_type", sa.String(), nullable=True),
        sa.Column("has_model_card", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("supports_https", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_auth", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("base_trust_score", sa.Float(), nullable=True),
        sa.Column("protected_score", sa.Float(), nullable=True),
        sa.Column("secure_mode_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("scan_status", sa.String(), nullable=True),
        sa.Column("scan_summary_json", sa.Text(), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    ]

    for column in model_columns:
        _add_column_if_missing(inspector, "models", column)

    for column_name in ("has_model_card", "supports_https", "requires_auth", "secure_mode_enabled"):
        if _has_column(inspector, "models", column_name):
            op.alter_column("models", column_name, server_default=None)

    if _has_column(inspector, "request_logs", "blocked"):
        op.alter_column("request_logs", "blocked", server_default=None)
    if _has_column(inspector, "request_logs", "secure_mode_enabled"):
        op.alter_column("request_logs", "secure_mode_enabled", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "request_logs"):
        op.drop_index(op.f("ix_request_logs_timestamp"), table_name="request_logs")
        op.drop_index(op.f("ix_request_logs_decision"), table_name="request_logs")
        op.drop_index(op.f("ix_request_logs_prompt_hash"), table_name="request_logs")
        op.drop_index(op.f("ix_request_logs_model_id"), table_name="request_logs")
        op.drop_index(op.f("ix_request_logs_id"), table_name="request_logs")
        op.drop_table("request_logs")

    for column_name in (
        "updated_at",
        "last_scan_at",
        "scan_summary_json",
        "scan_status",
        "secure_mode_enabled",
        "protected_score",
        "base_trust_score",
        "requires_auth",
        "supports_https",
        "has_model_card",
        "auth_type",
        "hf_model_id",
        "provider_name",
        "source_url",
    ):
        if _has_column(inspector, "models", column_name):
            op.drop_column("models", column_name)

    if _has_column(inspector, "users", "is_admin"):
        op.drop_column("users", "is_admin")
