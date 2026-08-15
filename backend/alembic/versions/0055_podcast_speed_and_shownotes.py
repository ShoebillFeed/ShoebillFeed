"""Add podcast speech_rate, cover image, description, and episode shownotes

Revision ID: 0055_podcast_speed_and_shownotes
Revises: 0054_add_podcast_public_feed
Create Date: 2026-08-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0055_podcast_speed_and_shownotes"
down_revision = "0054_add_podcast_public_feed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "podcast_shows",
        sa.Column("speech_rate", sa.Float(), nullable=False, server_default="1.0"),
    )
    op.add_column(
        "podcast_shows",
        sa.Column("cover_image_path", sa.Text(), nullable=True),
    )
    op.add_column(
        "podcast_shows",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "podcast_episodes",
        sa.Column("shownotes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("podcast_episodes", "shownotes")
    op.drop_column("podcast_shows", "description")
    op.drop_column("podcast_shows", "cover_image_path")
    op.drop_column("podcast_shows", "speech_rate")
