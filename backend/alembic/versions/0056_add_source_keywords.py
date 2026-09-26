"""Add news_items.source_keywords

Keywords a source supplies itself (arXiv subject categories) are kept in
their own column rather than written straight into extracted_keywords: LLM
processing overwrites that column wholesale, so anything stored there at
fetch time would be clobbered. They're merged into extracted_keywords at
processing time instead -- see tasks/process_tasks.py.

Revision ID: 0056_add_source_keywords
Revises: 0055_podcast_speed_and_shownotes
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0056_add_source_keywords"
down_revision = "0055_podcast_speed_and_shownotes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "news_items",
        sa.Column("source_keywords", postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("news_items", "source_keywords")
