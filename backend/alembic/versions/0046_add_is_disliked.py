"""Add is_disliked column to news_items

Revision ID: 0046_add_is_disliked
Revises: 0045_update_diversity_defaults
Create Date: 2026-06-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0046_add_is_disliked"
down_revision = "0045_update_diversity_defaults"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "news_items",
        sa.Column("is_disliked", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("news_items", "is_disliked")
