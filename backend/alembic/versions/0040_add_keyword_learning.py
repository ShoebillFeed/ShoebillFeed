"""Add category_keyword_weights and keyword_clusters tables

Revision ID: 0040_add_keyword_learning
Revises: 0039_add_category_taxonomy_id
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0040_add_keyword_learning"
down_revision = "0039_add_category_taxonomy_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "category_keyword_weights",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("keyword", sa.String(200), primary_key=True),
        sa.Column("starred_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "keyword_clusters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cluster_index", sa.Integer, nullable=False),
        sa.Column("keyword", sa.String(200), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("cluster_size", sa.Integer, nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_keyword_clusters_lookup", "keyword_clusters", ["user_id", "category_id", "keyword"])


def downgrade() -> None:
    op.drop_index("idx_keyword_clusters_lookup", table_name="keyword_clusters")
    op.drop_table("keyword_clusters")
    op.drop_table("category_keyword_weights")
