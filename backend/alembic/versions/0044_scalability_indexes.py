"""Add user_id to category_weights and composite feed indexes

Revision ID: 0044_scalability_indexes
Revises: 0043_add_diversity_settings
Create Date: 2026-06-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0044_scalability_indexes"
down_revision = "0043_add_diversity_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id to category_weights, populated from categories.user_id
    op.add_column("category_weights", sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True))
    op.execute("""
        UPDATE category_weights
        SET user_id = categories.user_id
        FROM categories
        WHERE categories.id = category_weights.category_id
    """)
    op.create_index("idx_category_weights_user_id", "category_weights", ["user_id"])

    # Composite feed query indexes
    op.create_index(
        "idx_news_items_feed",
        "news_items",
        ["user_id", "is_read", "cluster_id"],
    )
    op.create_index(
        "idx_news_items_user_published",
        "news_items",
        ["user_id", "published_at"],
    )
    op.create_index(
        "idx_news_clusters_feed",
        "news_clusters",
        ["user_id", "is_read"],
    )
    op.create_index(
        "idx_news_clusters_user_published",
        "news_clusters",
        ["user_id", "published_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_news_clusters_user_published", "news_clusters")
    op.drop_index("idx_news_clusters_feed", "news_clusters")
    op.drop_index("idx_news_items_user_published", "news_items")
    op.drop_index("idx_news_items_feed", "news_items")
    op.drop_index("idx_category_weights_user_id", "category_weights")
    op.drop_column("category_weights", "user_id")
