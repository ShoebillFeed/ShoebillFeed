"""add user_settings table

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("llm_min_word_count", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("weight_base", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("weight_log_multiplier", sa.Float(), nullable=False, server_default="0.5"),
    )


def downgrade() -> None:
    op.drop_table("user_settings")
