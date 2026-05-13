"""add attack sequence events

Revision ID: 6c8f2a9d1b77
Revises: 4d2f8e1b9c01
Create Date: 2026-04-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c8f2a9d1b77"
down_revision: Union[str, Sequence[str], None] = "4d2f8e1b9c01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _create_index_if_missing(inspector, table_name: str, index_name: str, columns: list[str]) -> None:
    if not _has_index(inspector, table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "attack_sequence_events"):
        op.create_table(
            "attack_sequence_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("model_id", sa.Integer(), nullable=True),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("attack_stage", sa.String(), nullable=False),
            sa.Column("decision", sa.String(), nullable=False),
            sa.Column("risk_score", sa.Float(), nullable=False),
            sa.Column("security_score", sa.Float(), nullable=False),
            sa.Column("sequence_severity", sa.Float(), nullable=False),
            sa.Column("repeated_pattern_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cross_model_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["model_id"], ["models.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing(inspector, "attack_sequence_events", "ix_attack_sequence_events_id", ["id"])
    _create_index_if_missing(inspector, "attack_sequence_events", "ix_attack_sequence_events_user_id", ["user_id"])
    _create_index_if_missing(inspector, "attack_sequence_events", "ix_attack_sequence_events_model_id", ["model_id"])
    _create_index_if_missing(inspector, "attack_sequence_events", "ix_attack_sequence_events_event_type", ["event_type"])
    _create_index_if_missing(inspector, "attack_sequence_events", "ix_attack_sequence_events_attack_stage", ["attack_stage"])
    _create_index_if_missing(inspector, "attack_sequence_events", "ix_attack_sequence_events_decision", ["decision"])
    _create_index_if_missing(inspector, "attack_sequence_events", "ix_attack_sequence_events_timestamp", ["timestamp"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for index_name in (
        "ix_attack_sequence_events_timestamp",
        "ix_attack_sequence_events_decision",
        "ix_attack_sequence_events_attack_stage",
        "ix_attack_sequence_events_event_type",
        "ix_attack_sequence_events_model_id",
        "ix_attack_sequence_events_user_id",
        "ix_attack_sequence_events_id",
    ):
        if _has_index(inspector, "attack_sequence_events", index_name):
            op.drop_index(index_name, table_name="attack_sequence_events")
    if _has_table(inspector, "attack_sequence_events"):
        op.drop_table("attack_sequence_events")
