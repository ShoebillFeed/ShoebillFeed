"""add composite indexes to news_clusters

Revision ID: 0049_news_cluster_indexes
Revises: 0048_add_cluster_label
Create Date: 2026-07-11

"""
from alembic import op

revision = "0049_news_cluster_indexes"
down_revision = "0048_add_cluster_label"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_news_clusters_user_published", "news_clusters", ["user_id", "published_at"])
    op.create_index("idx_news_clusters_user_is_read", "news_clusters", ["user_id", "is_read"])
    op.create_index(
        "idx_news_clusters_user_read_later",
        "news_clusters",
        ["user_id", "read_later"],
        postgresql_where="read_later = true",
    )


def downgrade() -> None:
    op.drop_index("idx_news_clusters_user_read_later", table_name="news_clusters")
    op.drop_index("idx_news_clusters_user_is_read", table_name="news_clusters")
    op.drop_index("idx_news_clusters_user_published", table_name="news_clusters")
