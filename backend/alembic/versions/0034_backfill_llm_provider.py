"""backfill llm_provider/llm_model for items processed before tracking existed

Revision ID: 0034_backfill_llm_provider
Revises: 0033_push_tab_filter
Create Date: 2026-06-10

"""
from alembic import op
import sqlalchemy as sa

from app.config import get_settings

revision = "0034_backfill_llm_provider"
down_revision = "0033_push_tab_filter"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Items/clusters processed before migration 0031 added llm_provider/llm_model
    have those columns NULL forever, since processed rows are never reprocessed.
    Backfill them with the currently configured primary provider as a best guess
    so the "info" tooltip has something to show."""
    settings = get_settings()
    provider = settings.llm_provider
    model = settings.anthropic_model if provider == "anthropic" else settings.ollama_model

    conn = op.get_bind()
    for table in ("news_items", "news_clusters"):
        conn.execute(
            sa.text(
                f"UPDATE {table} SET llm_provider = :provider, llm_model = :model "
                "WHERE llm_processed = true AND llm_provider IS NULL"
            ),
            {"provider": provider, "model": model},
        )


def downgrade() -> None:
    pass
