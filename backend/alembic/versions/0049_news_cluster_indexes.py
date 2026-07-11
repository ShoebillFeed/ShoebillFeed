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
    # idx_news_clusters_user_published and idx_news_clusters_feed (user_id, is_read)
    # were already created by 0044_scalability_indexes. Only add the missing partial index.
    op.create_index(
        "idx_news_clusters_user_read_later",
        "news_clusters",
        ["user_id", "read_later"],
        postgresql_where="read_later = true",
    )


def downgrade() -> None:
    op.drop_index("idx_news_clusters_user_read_later", table_name="news_clusters")
