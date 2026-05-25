"""multi-category: join tables for news_item and news_cluster categories

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_item_categories",
        sa.Column("news_item_id", UUID(as_uuid=True), sa.ForeignKey("news_items.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    )
    op.create_index("idx_nic_category_id", "news_item_categories", ["category_id"])

    op.create_table(
        "news_cluster_categories",
        sa.Column("news_cluster_id", UUID(as_uuid=True), sa.ForeignKey("news_clusters.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    )
    op.create_index("idx_ncc_category_id", "news_cluster_categories", ["category_id"])

    # Migrate existing single-category assignments
    op.execute("""
        INSERT INTO news_item_categories (news_item_id, category_id)
        SELECT id, category_id FROM news_items WHERE category_id IS NOT NULL
    """)
    op.execute("""
        INSERT INTO news_cluster_categories (news_cluster_id, category_id)
        SELECT id, category_id FROM news_clusters WHERE category_id IS NOT NULL
    """)

    op.drop_index("idx_news_items_category_id", table_name="news_items")
    op.drop_column("news_items", "category_id")
    op.drop_column("news_clusters", "category_id")


def downgrade() -> None:
    op.add_column("news_clusters", sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True))
    op.add_column("news_items", sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True))
    op.create_index("idx_news_items_category_id", "news_items", ["category_id"])

    # Restore first category only (lossy)
    op.execute("""
        UPDATE news_items ni
        SET category_id = nic.category_id
        FROM (SELECT DISTINCT ON (news_item_id) news_item_id, category_id FROM news_item_categories) nic
        WHERE ni.id = nic.news_item_id
    """)
    op.execute("""
        UPDATE news_clusters nc
        SET category_id = ncc.category_id
        FROM (SELECT DISTINCT ON (news_cluster_id) news_cluster_id, category_id FROM news_cluster_categories) ncc
        WHERE nc.id = ncc.news_cluster_id
    """)

    op.drop_index("idx_ncc_category_id", table_name="news_cluster_categories")
    op.drop_table("news_cluster_categories")
    op.drop_index("idx_nic_category_id", table_name="news_item_categories")
    op.drop_table("news_item_categories")
