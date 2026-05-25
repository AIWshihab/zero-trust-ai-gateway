"""add extension pairing tokens

Revision ID: 7dd9baf91c03
Revises: 2b7a6d0f4c21
Create Date: 2026-05-22 03:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7dd9baf91c03"
down_revision: Union[str, None] = "2b7a6d0f4c21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extension_pairing_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_extension_pairing_tokens_expires_at"), "extension_pairing_tokens", ["expires_at"], unique=False)
    op.create_index(op.f("ix_extension_pairing_tokens_id"), "extension_pairing_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_extension_pairing_tokens_token_hash"), "extension_pairing_tokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_extension_pairing_tokens_user_id"), "extension_pairing_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_extension_pairing_tokens_user_id"), table_name="extension_pairing_tokens")
    op.drop_index(op.f("ix_extension_pairing_tokens_token_hash"), table_name="extension_pairing_tokens")
    op.drop_index(op.f("ix_extension_pairing_tokens_id"), table_name="extension_pairing_tokens")
    op.drop_index(op.f("ix_extension_pairing_tokens_expires_at"), table_name="extension_pairing_tokens")
    op.drop_table("extension_pairing_tokens")
