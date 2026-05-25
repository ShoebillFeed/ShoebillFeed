"""add news clusters

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("unified_abstract", sa.Text(), nullable=True),
        sa.Column("relevance_score", sa.SmallInteger(), nullable=True),
        sa.Column("impact_score", sa.SmallInteger(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_relevant", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_later", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("llm_processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.add_column(
        "news_items",
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("news_clusters.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "news_items",
        sa.Column("source_summary", sa.Text(), nullable=True),
    )
    op.create_index("idx_news_items_cluster_id", "news_items", ["cluster_id"])


def downgrade() -> None:
    op.drop_index("idx_news_items_cluster_id", "news_items")
    op.drop_column("news_items", "source_summary")
    op.drop_column("news_items", "cluster_id")
    op.drop_table("news_clusters")
