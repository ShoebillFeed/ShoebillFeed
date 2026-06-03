"""add show_count to news_items and news_clusters

Revision ID: 0021
Revises: 0020
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "news_items",
        sa.Column("show_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "news_clusters",
        sa.Column("show_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("news_clusters", "show_count")
    op.drop_column("news_items", "show_count")
