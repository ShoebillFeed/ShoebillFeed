"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6366f1"),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "category_weights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("total_marked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("fetch_interval", sa.Integer(), nullable=False, server_default="3600"),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "news_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("url_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("relevance_score", sa.SmallInteger(), nullable=True),
        sa.Column("impact_score", sa.SmallInteger(), nullable=True),
        sa.Column("llm_processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_relevant", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_later", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("idx_news_items_source_id", "news_items", ["source_id"])
    op.create_index("idx_news_items_category_id", "news_items", ["category_id"])
    op.create_index("idx_news_items_published_at", "news_items", ["published_at"])
    op.create_index(
        "idx_news_items_relevance", "news_items", ["relevance_score"],
        postgresql_where=sa.text("llm_processed = true"),
    )
    op.create_index(
        "idx_news_items_impact", "news_items", ["impact_score"],
        postgresql_where=sa.text("llm_processed = true"),
    )
    op.create_index(
        "idx_news_items_read_later", "news_items", ["read_later"],
        postgresql_where=sa.text("read_later = true"),
    )


def downgrade() -> None:
    op.drop_table("news_items")
    op.drop_table("sources")
    op.drop_table("category_weights")
    op.drop_table("categories")
