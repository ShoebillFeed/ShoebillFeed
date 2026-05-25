"""add extracted_keywords and keyword_weights table

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("news_items", sa.Column("extracted_keywords", postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column("news_clusters", sa.Column("extracted_keywords", postgresql.ARRAY(sa.String()), nullable=True))
    op.create_table(
        "keyword_weights",
        sa.Column("keyword", sa.String(200), primary_key=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("total_marked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("keyword_weights")
    op.drop_column("news_clusters", "extracted_keywords")
    op.drop_column("news_items", "extracted_keywords")
