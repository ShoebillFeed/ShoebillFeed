"""change url_hash uniqueness from global to per-user

Revision ID: 0024
Revises: 0023
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old global unique constraint
    op.drop_constraint("news_items_url_hash_key", "news_items", type_="unique")
    # Per-user uniqueness: the same URL can exist once per user
    op.create_unique_constraint("uq_news_items_user_url", "news_items", ["user_id", "url_hash"])
    # Keep a plain index on url_hash alone so cross-user lookups stay fast
    op.create_index("idx_news_items_url_hash", "news_items", ["url_hash"])


def downgrade() -> None:
    op.drop_index("idx_news_items_url_hash", table_name="news_items")
    op.drop_constraint("uq_news_items_user_url", "news_items", type_="unique")
    op.create_unique_constraint("news_items_url_hash_key", "news_items", ["url_hash"])
