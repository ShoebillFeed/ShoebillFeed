"""add push_top_category_percent to user_settings

Revision ID: 0036_push_top_category_percent
Revises: 0035_notified_at
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa

revision = "0036_push_top_category_percent"
down_revision = "0035_notified_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("push_top_category_percent", sa.Float(), nullable=False, server_default="100.0"),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "push_top_category_percent")
