"""Add podcast_shows and podcast_episodes tables

Revision ID: 0053_add_podcasts
Revises: 0052_add_user_tab_icon
Create Date: 2026-07-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

revision = "0053_add_podcasts"
down_revision = "0052_add_user_tab_icon"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "podcast_shows",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("hosts", JSONB, nullable=False, server_default="[]"),
        sa.Column("category_ids", ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("source_ids", ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("time_window_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("target_length_minutes", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("schedule_time", sa.String(5), nullable=False, server_default="07:00"),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "podcast_episodes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("show_id", UUID(as_uuid=True), sa.ForeignKey("podcast_shows.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("script", JSONB, nullable=True),
        sa.Column("news_item_ids", ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("news_cluster_ids", ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("audio_path", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_podcast_episodes_show_created", "podcast_episodes", ["show_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_podcast_episodes_show_created", table_name="podcast_episodes")
    op.drop_table("podcast_episodes")
    op.drop_table("podcast_shows")
