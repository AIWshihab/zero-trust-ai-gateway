"""add extension setup sessions

Revision ID: 8c4d2e1f9a10
Revises: 7dd9baf91c03
Create Date: 2026-05-22 04:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c4d2e1f9a10"
down_revision: Union[str, None] = "7dd9baf91c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("extension_pairing_tokens", sa.Column("setup_session_id", sa.String(length=64), nullable=True))
    op.add_column("extension_pairing_tokens", sa.Column("registered_device_id", sa.Integer(), nullable=True))
    op.add_column("extension_pairing_tokens", sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("extension_pairing_tokens", sa.Column("browser_name", sa.String(length=80), nullable=True))
    op.add_column("extension_pairing_tokens", sa.Column("extension_version", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_extension_pairing_tokens_registered_device_id_devices",
        "extension_pairing_tokens",
        "devices",
        ["registered_device_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_extension_pairing_tokens_setup_session_id"), "extension_pairing_tokens", ["setup_session_id"], unique=True)
    op.create_index(op.f("ix_extension_pairing_tokens_registered_device_id"), "extension_pairing_tokens", ["registered_device_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_extension_pairing_tokens_registered_device_id"), table_name="extension_pairing_tokens")
    op.drop_index(op.f("ix_extension_pairing_tokens_setup_session_id"), table_name="extension_pairing_tokens")
    op.drop_constraint("fk_extension_pairing_tokens_registered_device_id_devices", "extension_pairing_tokens", type_="foreignkey")
    op.drop_column("extension_pairing_tokens", "extension_version")
    op.drop_column("extension_pairing_tokens", "browser_name")
    op.drop_column("extension_pairing_tokens", "connected_at")
    op.drop_column("extension_pairing_tokens", "registered_device_id")
    op.drop_column("extension_pairing_tokens", "setup_session_id")
