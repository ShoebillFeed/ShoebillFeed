"""add learning_window_days to user_settings

Revision ID: 0026_learning_window_days
Revises: 0025_mark_shown_delay
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa

revision = "0026_learning_window_days"
down_revision = "0025_mark_shown_delay"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("learning_window_days", sa.Integer(), nullable=False, server_default="90"),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "learning_window_days")
