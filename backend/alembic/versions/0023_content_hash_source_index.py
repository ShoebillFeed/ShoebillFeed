"""index on (source_id, content_hash) for content-based deduplication

Revision ID: 0023
Revises: 0022
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_news_items_source_content_hash",
        "news_items",
        ["source_id", "content_hash"],
        postgresql_where=sa.text("content_hash IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_news_items_source_content_hash", table_name="news_items")
