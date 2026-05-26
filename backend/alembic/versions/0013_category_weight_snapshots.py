"""add category_weight_snapshots

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "category_weight_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("total_marked", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_cw_snapshots_category_recorded", "category_weight_snapshots", ["category_id", "recorded_at"])


def downgrade() -> None:
    op.drop_index("idx_cw_snapshots_category_recorded")
    op.drop_table("category_weight_snapshots")
