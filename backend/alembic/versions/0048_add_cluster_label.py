"""Add cluster_label to keyword_clusters

Revision ID: 0048_add_cluster_label
Revises: 0047_add_api_tokens
Create Date: 2026-06-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0048_add_cluster_label"
down_revision = "0047_add_api_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "keyword_clusters",
        sa.Column("cluster_label", sa.String(300), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("keyword_clusters", "cluster_label")
