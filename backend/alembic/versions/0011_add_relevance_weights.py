"""add relevance weights to user_settings

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("relevance_llm_weight", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("user_settings", sa.Column("relevance_learning_weight", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("user_settings", sa.Column("relevance_cluster_weight", sa.Float(), nullable=False, server_default="0.5"))


def downgrade() -> None:
    op.drop_column("user_settings", "relevance_cluster_weight")
    op.drop_column("user_settings", "relevance_learning_weight")
    op.drop_column("user_settings", "relevance_llm_weight")
