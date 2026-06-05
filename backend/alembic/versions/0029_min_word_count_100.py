"""raise llm_min_word_count default to 100

Revision ID: 0029_min_word_count_100
Revises: 0028_llm_batch
Create Date: 2026-06-05

"""
from alembic import op
import sqlalchemy as sa

revision = "0029_min_word_count_100"
down_revision = "0028_llm_batch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "user_settings",
        "llm_min_word_count",
        existing_type=sa.Integer(),
        server_default="100",
        existing_nullable=False,
    )
    op.execute("UPDATE user_settings SET llm_min_word_count = 100 WHERE llm_min_word_count <= 50")


def downgrade() -> None:
    op.alter_column(
        "user_settings",
        "llm_min_word_count",
        existing_type=sa.Integer(),
        server_default="50",
        existing_nullable=False,
    )
