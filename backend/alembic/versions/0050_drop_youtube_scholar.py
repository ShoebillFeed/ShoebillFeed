"""Retire the youtube source type and the scholar alias for arxiv

The youtube and scholar (arxiv-alias) fetchers have been removed from the
codebase. Existing rows with these source_types would otherwise be
unfetchable (get_fetcher() raises for an unregistered type) and retry
indefinitely. This migration:
  - deactivates existing 'youtube' sources (preserves history/read items,
    just stops further fetch attempts -- there's no equivalent type to
    migrate them to)
  - renames existing 'scholar' sources to 'arxiv' (the same fetcher
    class handled both identically, so this is a like-for-like rename,
    not a behavior change)

Revision ID: 0050_drop_youtube_scholar
Revises: 0049_news_cluster_indexes
Create Date: 2026-07-14

"""
from alembic import op

revision = "0050_drop_youtube_scholar"
down_revision = "0049_news_cluster_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE sources SET is_active = false WHERE source_type = 'youtube'"
    )
    op.execute(
        "UPDATE sources SET source_type = 'arxiv' WHERE source_type = 'scholar'"
    )


def downgrade() -> None:
    # Not reversible: we can't tell which 'arxiv' rows were originally
    # 'scholar', and we don't want to silently reactivate youtube sources
    # whose fetcher no longer exists in the codebase at this revision.
    pass
