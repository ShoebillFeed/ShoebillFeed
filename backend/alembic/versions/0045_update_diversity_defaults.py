"""Update existing user_settings rows to new diversity defaults

Revision ID: 0045_update_diversity_defaults
Revises: 0044_scalability_indexes
Create Date: 2026-06-24
"""
from alembic import op

revision = "0045_update_diversity_defaults"
down_revision = "0044_scalability_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE user_settings SET max_per_category = 6 WHERE max_per_category = 8"
    )
    op.execute(
        "UPDATE user_settings SET exploration_fraction = 0.1 WHERE exploration_fraction = 0.05"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE user_settings SET max_per_category = 8 WHERE max_per_category = 6"
    )
    op.execute(
        "UPDATE user_settings SET exploration_fraction = 0.05 WHERE exploration_fraction = 0.1"
    )
