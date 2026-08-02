"""Add public feed link fields to podcast_shows

Revision ID: 0054_add_podcast_public_feed
Revises: 0053_add_podcasts
Create Date: 2026-08-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0054_add_podcast_public_feed"
down_revision = "0053_add_podcasts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("podcast_shows", sa.Column("public_feed_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("podcast_shows", sa.Column("public_feed_token", sa.String(64), nullable=True))
    op.create_index("ix_podcast_shows_public_feed_token", "podcast_shows", ["public_feed_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_podcast_shows_public_feed_token", table_name="podcast_shows")
    op.drop_column("podcast_shows", "public_feed_token")
    op.drop_column("podcast_shows", "public_feed_enabled")
