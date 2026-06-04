"""add ignore_penalty_weight to user_settings

Revision ID: 0027_ignore_penalty_weight
Revises: 0026_learning_window_days
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa

revision = "0027_ignore_penalty_weight"
down_revision = "0026_learning_window_days"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("ignore_penalty_weight", sa.Float(), nullable=False, server_default="0.1"),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "ignore_penalty_weight")
