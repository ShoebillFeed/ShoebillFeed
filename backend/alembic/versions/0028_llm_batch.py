"""add llm_batches table for Anthropic batch API

Revision ID: 0028_llm_batch
Revises: 0027_ignore_penalty_weight
Create Date: 2026-06-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "0028_llm_batch"
down_revision = "0027_ignore_penalty_weight"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_batches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("anthropic_batch_id", sa.String(128), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("requests", JSON, nullable=False),
    )
    op.create_index("ix_llm_batches_anthropic_batch_id", "llm_batches", ["anthropic_batch_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_llm_batches_anthropic_batch_id", table_name="llm_batches")
    op.drop_table("llm_batches")
