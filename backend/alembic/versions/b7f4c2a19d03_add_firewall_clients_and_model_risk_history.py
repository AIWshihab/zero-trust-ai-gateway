"""add firewall clients and model risk history

Revision ID: b7f4c2a19d03
Revises: 6c8f2a9d1b77
Create Date: 2026-05-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7f4c2a19d03"
down_revision: Union[str, Sequence[str], None] = "6c8f2a9d1b77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _create_index_if_missing(inspector, table_name: str, index_name: str, columns: list[str], *, unique: bool = False) -> None:
    if not _has_index(inspector, table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "firewall_clients"):
        op.create_table(
            "firewall_clients",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("client_id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("api_key_hash", sa.String(), nullable=False),
            sa.Column("hmac_secret", sa.Text(), nullable=True),
            sa.Column("require_signature", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("rate_limit", sa.Integer(), nullable=False, server_default="60"),
            sa.Column("rate_window_seconds", sa.Integer(), nullable=False, server_default="60"),
            sa.Column("trust_score", sa.Float(), nullable=False, server_default="0.8"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table(inspector, "model_risk_history"):
        op.create_table(
            "model_risk_history",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("model_id", sa.Integer(), nullable=False),
            sa.Column("prompt_hash", sa.String(), nullable=False),
            sa.Column("decision", sa.String(), nullable=False),
            sa.Column("prompt_risk_score", sa.Float(), nullable=True),
            sa.Column("output_risk_score", sa.Float(), nullable=True),
            sa.Column("security_score", sa.Float(), nullable=True),
            sa.Column("effective_risk", sa.Float(), nullable=True),
            sa.Column("response_safety_score", sa.Float(), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("comparison_group", sa.String(), nullable=True),
            sa.Column("context_json", sa.JSON(), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["model_id"], ["models.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing(inspector, "firewall_clients", "ix_firewall_clients_id", ["id"])
    _create_index_if_missing(inspector, "firewall_clients", "ix_firewall_clients_client_id", ["client_id"], unique=True)
    _create_index_if_missing(inspector, "firewall_clients", "ix_firewall_clients_api_key_hash", ["api_key_hash"], unique=True)
    _create_index_if_missing(inspector, "firewall_clients", "ix_firewall_clients_is_active", ["is_active"])
    _create_index_if_missing(inspector, "model_risk_history", "ix_model_risk_history_id", ["id"])
    _create_index_if_missing(inspector, "model_risk_history", "ix_model_risk_history_model_id", ["model_id"])
    _create_index_if_missing(inspector, "model_risk_history", "ix_model_risk_history_prompt_hash", ["prompt_hash"])
    _create_index_if_missing(inspector, "model_risk_history", "ix_model_risk_history_decision", ["decision"])
    _create_index_if_missing(inspector, "model_risk_history", "ix_model_risk_history_comparison_group", ["comparison_group"])
    _create_index_if_missing(inspector, "model_risk_history", "ix_model_risk_history_timestamp", ["timestamp"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for index_name in (
        "ix_model_risk_history_timestamp",
        "ix_model_risk_history_comparison_group",
        "ix_model_risk_history_decision",
        "ix_model_risk_history_prompt_hash",
        "ix_model_risk_history_model_id",
        "ix_model_risk_history_id",
    ):
        if _has_index(inspector, "model_risk_history", index_name):
            op.drop_index(index_name, table_name="model_risk_history")
    if _has_table(inspector, "model_risk_history"):
        op.drop_table("model_risk_history")

    for index_name in (
        "ix_firewall_clients_is_active",
        "ix_firewall_clients_api_key_hash",
        "ix_firewall_clients_client_id",
        "ix_firewall_clients_id",
    ):
        if _has_index(inspector, "firewall_clients", index_name):
            op.drop_index(index_name, table_name="firewall_clients")
    if _has_table(inspector, "firewall_clients"):
        op.drop_table("firewall_clients")
