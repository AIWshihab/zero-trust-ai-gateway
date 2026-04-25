"""add dynamic security control plane

Revision ID: 4d2f8e1b9c01
Revises: 91a0f3d8b2b4
Create Date: 2026-04-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4d2f8e1b9c01"
down_revision: Union[str, Sequence[str], None] = "91a0f3d8b2b4"
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

    if not _has_table(inspector, "security_controls"):
        op.create_table(
            "security_controls",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("control_id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("framework", sa.String(), nullable=False),
            sa.Column("coverage", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("control_family", sa.String(), nullable=True),
            sa.Column("mapped_capabilities", sa.JSON(), nullable=True),
            sa.Column("recommended_actions", sa.JSON(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("control_id", name="uq_security_controls_control_id"),
        )

    _create_index_if_missing(inspector, "security_controls", "ix_security_controls_id", ["id"])
    _create_index_if_missing(inspector, "security_controls", "ix_security_controls_control_id", ["control_id"], unique=True)
    _create_index_if_missing(inspector, "security_controls", "ix_security_controls_name", ["name"])
    _create_index_if_missing(inspector, "security_controls", "ix_security_controls_coverage", ["coverage"])
    _create_index_if_missing(inspector, "security_controls", "ix_security_controls_status", ["status"])
    _create_index_if_missing(inspector, "security_controls", "ix_security_controls_control_family", ["control_family"])
    _create_index_if_missing(inspector, "security_controls", "ix_security_controls_enabled", ["enabled"])

    if not _has_table(inspector, "detection_rules"):
        op.create_table(
            "detection_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("target", sa.String(), nullable=False),
            sa.Column("match_type", sa.String(), nullable=False),
            sa.Column("pattern", sa.Text(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("decision", sa.String(), nullable=False),
            sa.Column("risk_delta", sa.Float(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing(inspector, "detection_rules", "ix_detection_rules_id", ["id"])
    _create_index_if_missing(inspector, "detection_rules", "ix_detection_rules_name", ["name"])
    _create_index_if_missing(inspector, "detection_rules", "ix_detection_rules_target", ["target"])
    _create_index_if_missing(inspector, "detection_rules", "ix_detection_rules_severity", ["severity"])
    _create_index_if_missing(inspector, "detection_rules", "ix_detection_rules_decision", ["decision"])
    _create_index_if_missing(inspector, "detection_rules", "ix_detection_rules_enabled", ["enabled"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for index_name in (
        "ix_detection_rules_enabled",
        "ix_detection_rules_decision",
        "ix_detection_rules_severity",
        "ix_detection_rules_target",
        "ix_detection_rules_name",
        "ix_detection_rules_id",
    ):
        if _has_index(inspector, "detection_rules", index_name):
            op.drop_index(index_name, table_name="detection_rules")
    if _has_table(inspector, "detection_rules"):
        op.drop_table("detection_rules")

    for index_name in (
        "ix_security_controls_enabled",
        "ix_security_controls_control_family",
        "ix_security_controls_status",
        "ix_security_controls_coverage",
        "ix_security_controls_name",
        "ix_security_controls_control_id",
        "ix_security_controls_id",
    ):
        if _has_index(inspector, "security_controls", index_name):
            op.drop_index(index_name, table_name="security_controls")
    if _has_table(inspector, "security_controls"):
        op.drop_table("security_controls")
