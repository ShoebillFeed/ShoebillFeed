"""add manual_weight to category_weights

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "category_weights",
        sa.Column("manual_weight", sa.Float(), nullable=False, server_default="1.0"),
    )


def downgrade() -> None:
    op.drop_column("category_weights", "manual_weight")
