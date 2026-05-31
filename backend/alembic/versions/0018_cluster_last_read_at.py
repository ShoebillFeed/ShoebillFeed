"""add last_read_at to news_clusters

Revision ID: 0018
Revises: 0017
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "news_clusters",
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("news_clusters", "last_read_at")
