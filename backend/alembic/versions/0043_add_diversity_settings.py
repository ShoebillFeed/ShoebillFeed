"""Add feed diversity settings to user_settings

Revision ID: 0043_add_diversity_settings
Revises: 0042_add_weight_decay_days
Create Date: 2026-06-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0043_add_diversity_settings"
down_revision = "0042_add_weight_decay_days"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("max_per_category", sa.Integer, nullable=False, server_default="8"))
    op.add_column("user_settings", sa.Column("max_per_source", sa.Integer, nullable=False, server_default="5"))
    op.add_column("user_settings", sa.Column("exploration_fraction", sa.Float, nullable=False, server_default="0.05"))


def downgrade() -> None:
    op.drop_column("user_settings", "max_per_category")
    op.drop_column("user_settings", "max_per_source")
    op.drop_column("user_settings", "exploration_fraction")
