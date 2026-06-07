"""add llm_provider and llm_model to news_items and news_clusters

Revision ID: 0031_llm_provider_tracking
Revises: 0030_mark_shown_delay_2
Create Date: 2026-06-07

"""
from alembic import op
import sqlalchemy as sa

revision = "0031_llm_provider_tracking"
down_revision = "0030_mark_shown_delay_2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("news_items", sa.Column("llm_provider", sa.String(64), nullable=True))
    op.add_column("news_items", sa.Column("llm_model", sa.String(128), nullable=True))
    op.add_column("news_clusters", sa.Column("llm_provider", sa.String(64), nullable=True))
    op.add_column("news_clusters", sa.Column("llm_model", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("news_clusters", "llm_model")
    op.drop_column("news_clusters", "llm_provider")
    op.drop_column("news_items", "llm_model")
    op.drop_column("news_items", "llm_provider")
