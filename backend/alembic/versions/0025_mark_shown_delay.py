"""add mark_shown_delay_seconds to user_settings

Revision ID: 0025_mark_shown_delay
Revises: 0024_per_user_url_hash
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa

revision = "0025_mark_shown_delay"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("mark_shown_delay_seconds", sa.Integer(), nullable=False, server_default="5"),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "mark_shown_delay_seconds")
