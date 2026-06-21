"""Add taxonomy_id column to categories

Revision ID: 0039_add_category_taxonomy_id
Revises: 0038_add_news_item_embedding
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0039_add_category_taxonomy_id"
down_revision = "0038_add_news_item_embedding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("taxonomy_id", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("categories", "taxonomy_id")
