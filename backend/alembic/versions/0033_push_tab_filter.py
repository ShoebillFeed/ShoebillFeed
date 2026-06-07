"""add push tab filter fields

Revision ID: 0033
Revises: 0032
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("push_all_tabs", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("user_settings", sa.Column("push_tab_ids", JSONB(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("user_settings", "push_tab_ids")
    op.drop_column("user_settings", "push_all_tabs")
