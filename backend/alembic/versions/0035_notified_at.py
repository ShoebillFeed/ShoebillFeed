"""add notified_at to news_items to dedupe push notifications

Revision ID: 0035_notified_at
Revises: 0034_backfill_llm_provider
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa

revision = "0035_notified_at"
down_revision = "0034_backfill_llm_provider"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("news_items", sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True))

    # Backfill: items already processed before this migration have already been
    # considered for notification under the old logic. Mark them as notified so
    # they aren't re-pushed the next time their cluster is reprocessed.
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE news_items SET notified_at = fetched_at WHERE llm_processed = true"))


def downgrade() -> None:
    op.drop_column("news_items", "notified_at")
