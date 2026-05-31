"""add output_language to user_settings

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("output_language", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "output_language")
