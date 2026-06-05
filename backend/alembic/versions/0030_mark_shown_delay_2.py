"""lower mark_shown_delay_seconds default to 2

Revision ID: 0030_mark_shown_delay_2
Revises: 0029_min_word_count_100
Create Date: 2026-06-05

"""
from alembic import op
import sqlalchemy as sa

revision = "0030_mark_shown_delay_2"
down_revision = "0029_min_word_count_100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "user_settings",
        "mark_shown_delay_seconds",
        existing_type=sa.Integer(),
        server_default="2",
        existing_nullable=False,
    )
    op.execute("UPDATE user_settings SET mark_shown_delay_seconds = 2 WHERE mark_shown_delay_seconds = 5")


def downgrade() -> None:
    op.alter_column(
        "user_settings",
        "mark_shown_delay_seconds",
        existing_type=sa.Integer(),
        server_default="5",
        existing_nullable=False,
    )
