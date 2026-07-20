"""Drop keyword_cluster_snapshots table

The "Keyword cluster scores" history chart (Settings -> Statistics) has
been removed. This table only ever fed that chart -- it's not read by
feed ranking or clustering, which use the keyword_clusters table
directly. Safe to drop.

Revision ID: 0051_drop_kw_cluster_snapshots
Revises: 0050_drop_youtube_scholar
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0051_drop_kw_cluster_snapshots"
down_revision = "0050_drop_youtube_scholar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("idx_kc_snapshots_lookup", table_name="keyword_cluster_snapshots")
    op.drop_table("keyword_cluster_snapshots")


def downgrade() -> None:
    op.create_table(
        "keyword_cluster_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cluster_label", sa.String(200), nullable=False),
        sa.Column("weight", sa.Float, nullable=False),
        sa.Column("cluster_size", sa.Integer, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_kc_snapshots_lookup", "keyword_cluster_snapshots", ["user_id", "recorded_at"])
