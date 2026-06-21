"""Add embedding vector column to news_items

Revision ID: 0038_add_news_item_embedding
Revises: 0037_normalize_keyword_weights
Create Date: 2026-06-21
"""
from alembic import op

revision = "0038_add_news_item_embedding"
down_revision = "0037_normalize_keyword_weights"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE news_items ADD COLUMN IF NOT EXISTS embedding vector(768)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_news_items_embedding "
        "ON news_items USING hnsw (embedding vector_cosine_ops) "
        "WITH (m=16, ef_construction=64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_news_items_embedding")
    op.execute("ALTER TABLE news_items DROP COLUMN IF EXISTS embedding")
