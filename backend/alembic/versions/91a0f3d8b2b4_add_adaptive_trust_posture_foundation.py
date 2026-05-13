"""add adaptive trust posture foundation

Revision ID: 91a0f3d8b2b4
Revises: f31e3f2a7b9d
Create Date: 2026-04-16 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "91a0f3d8b2b4"
down_revision: Union[str, Sequence[str], None] = "f31e3f2a7b9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _add_column_if_missing(inspector, table_name: str, column: sa.Column) -> None:
    if not _has_column(inspector, table_name, column.name):
        op.add_column(table_name, column)


def _create_index_if_missing(inspector, table_name: str, index_name: str, columns: list[str]) -> None:
    if not _has_index(inspector, table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    model_columns = [
        sa.Column("base_risk_score", sa.Float(), nullable=True),
        sa.Column("secured_risk_score", sa.Float(), nullable=True),
        sa.Column("risk_reduction_pct", sa.Float(), nullable=True),
        sa.Column("posture_factors", sa.JSON(), nullable=True),
        sa.Column("posture_explanations", sa.JSON(), nullable=True),
        sa.Column("posture_assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posture_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reassessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scan_valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scan_freshness_days", sa.Integer(), nullable=True),
    ]

    for column in model_columns:
        _add_column_if_missing(inspector, "models", column)

    request_log_columns = [
        sa.Column("decision_input_snapshot", sa.JSON(), nullable=True),
        sa.Column("decision_trace", sa.JSON(), nullable=True),
    ]

    for column in request_log_columns:
        _add_column_if_missing(inspector, "request_logs", column)

    if not _has_table(inspector, "user_trust_events"):
        op.create_table(
            "user_trust_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("username_snapshot", sa.String(), nullable=False),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("previous_value", sa.Float(), nullable=True),
            sa.Column("new_value", sa.Float(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("context_json", sa.JSON(), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing(inspector, "user_trust_events", "ix_user_trust_events_id", ["id"])
    _create_index_if_missing(inspector, "user_trust_events", "ix_user_trust_events_user_id", ["user_id"])
    _create_index_if_missing(inspector, "user_trust_events", "ix_user_trust_events_username_snapshot", ["username_snapshot"])
    _create_index_if_missing(inspector, "user_trust_events", "ix_user_trust_events_event_type", ["event_type"])
    _create_index_if_missing(inspector, "user_trust_events", "ix_user_trust_events_timestamp", ["timestamp"])

    if not _has_table(inspector, "model_posture_events"):
        op.create_table(
            "model_posture_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("model_id", sa.Integer(), nullable=False),
            sa.Column("model_name_snapshot", sa.String(), nullable=True),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("metric_name", sa.String(), nullable=False),
            sa.Column("previous_value", sa.Float(), nullable=True),
            sa.Column("new_value", sa.Float(), nullable=True),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("context_json", sa.JSON(), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["model_id"], ["models.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing(inspector, "model_posture_events", "ix_model_posture_events_id", ["id"])
    _create_index_if_missing(inspector, "model_posture_events", "ix_model_posture_events_model_id", ["model_id"])
    _create_index_if_missing(inspector, "model_posture_events", "ix_model_posture_events_event_type", ["event_type"])
    _create_index_if_missing(inspector, "model_posture_events", "ix_model_posture_events_metric_name", ["metric_name"])
    _create_index_if_missing(inspector, "model_posture_events", "ix_model_posture_events_timestamp", ["timestamp"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for index_name in (
        "ix_model_posture_events_timestamp",
        "ix_model_posture_events_metric_name",
        "ix_model_posture_events_event_type",
        "ix_model_posture_events_model_id",
        "ix_model_posture_events_id",
    ):
        if _has_index(inspector, "model_posture_events", index_name):
            op.drop_index(index_name, table_name="model_posture_events")

    if _has_table(inspector, "model_posture_events"):
        op.drop_table("model_posture_events")

    for index_name in (
        "ix_user_trust_events_timestamp",
        "ix_user_trust_events_event_type",
        "ix_user_trust_events_username_snapshot",
        "ix_user_trust_events_user_id",
        "ix_user_trust_events_id",
    ):
        if _has_index(inspector, "user_trust_events", index_name):
            op.drop_index(index_name, table_name="user_trust_events")

    if _has_table(inspector, "user_trust_events"):
        op.drop_table("user_trust_events")

    for column_name in ("decision_trace", "decision_input_snapshot"):
        if _has_column(inspector, "request_logs", column_name):
            op.drop_column("request_logs", column_name)

    for column_name in (
        "scan_freshness_days",
        "scan_valid_until",
        "last_reassessed_at",
        "posture_expires_at",
        "posture_assessed_at",
        "posture_explanations",
        "posture_factors",
        "risk_reduction_pct",
        "secured_risk_score",
        "base_risk_score",
    ):
        if _has_column(inspector, "models", column_name):
            op.drop_column("models", column_name)
