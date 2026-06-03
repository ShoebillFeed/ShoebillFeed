"""raise llm_min_word_count default to 50

Revision ID: 0022
Revises: 0021
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "user_settings",
        "llm_min_word_count",
        existing_type=sa.Integer(),
        server_default="50",
        existing_nullable=False,
    )
    op.execute("UPDATE user_settings SET llm_min_word_count = 50 WHERE llm_min_word_count < 50")


def downgrade() -> None:
    op.alter_column(
        "user_settings",
        "llm_min_word_count",
        existing_type=sa.Integer(),
        server_default="40",
        existing_nullable=False,
    )
