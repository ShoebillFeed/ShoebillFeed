"""Add weight_decay_days to user_settings

Revision ID: 0042_add_weight_decay_days
Revises: 0041_kw_cluster_snapshots
Create Date: 2026-06-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0042_add_weight_decay_days"
down_revision = "0041_kw_cluster_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("weight_decay_days", sa.Integer, nullable=False, server_default="60"),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "weight_decay_days")
