"""Add icon column to user_tabs

Revision ID: 0052_add_user_tab_icon
Revises: 0051_drop_kw_cluster_snapshots
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0052_add_user_tab_icon"
down_revision = "0051_drop_kw_cluster_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_tabs", sa.Column("icon", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("user_tabs", "icon")
