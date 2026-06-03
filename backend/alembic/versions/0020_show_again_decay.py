"""add show-again decay columns

Revision ID: 0020
Revises: 0019
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "news_items",
        sa.Column("last_shown_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "news_clusters",
        sa.Column("last_shown_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_settings",
        sa.Column("show_decay_param", sa.Float(), nullable=False, server_default="0.0"),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "show_decay_param")
    op.drop_column("news_clusters", "last_shown_at")
    op.drop_column("news_items", "last_shown_at")
