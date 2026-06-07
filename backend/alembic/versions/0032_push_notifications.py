"""add push notification settings and subscriptions table

Revision ID: 0032_push_notifications
Revises: 0031_llm_provider_tracking
Create Date: 2026-06-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0032_push_notifications"
down_revision = "0031_llm_provider_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint", sa.Text, nullable=False),
        sa.Column("p256dh", sa.String(256), nullable=False),
        sa.Column("auth", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_push_subscriptions_user_id", "push_subscriptions", ["user_id"])

    op.add_column("user_settings", sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("user_settings", sa.Column("push_min_relevance", sa.Integer(), nullable=False, server_default="7"))
    op.add_column("user_settings", sa.Column("push_all_categories", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("user_settings", sa.Column("push_category_ids", postgresql.JSONB(), nullable=False, server_default="[]"))
    op.add_column("user_settings", sa.Column("push_all_sources", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("user_settings", sa.Column("push_source_ids", postgresql.JSONB(), nullable=False, server_default="[]"))
    op.add_column("user_settings", sa.Column("push_cluster_per_source", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("user_settings", "push_cluster_per_source")
    op.drop_column("user_settings", "push_source_ids")
    op.drop_column("user_settings", "push_all_sources")
    op.drop_column("user_settings", "push_category_ids")
    op.drop_column("user_settings", "push_all_categories")
    op.drop_column("user_settings", "push_min_relevance")
    op.drop_column("user_settings", "push_enabled")
    op.drop_index("idx_push_subscriptions_user_id", "push_subscriptions")
    op.drop_table("push_subscriptions")
