"""add users table and user_id to all data tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])

    for table in ("sources", "categories", "news_items", "news_clusters"):
        op.add_column(
            table,
            sa.Column("user_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])

    # Remove unique constraint on category name (now scoped per user)
    op.drop_constraint("categories_name_key", "categories", type_="unique")

    # Recreate keyword_weights with composite PK (user_id, keyword)
    op.drop_table("keyword_weights")
    op.create_table(
        "keyword_weights",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("keyword", sa.String(200), primary_key=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("total_marked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("keyword_weights")
    op.create_table(
        "keyword_weights",
        sa.Column("keyword", sa.String(200), primary_key=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("total_marked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    for table in ("news_clusters", "news_items", "categories", "sources"):
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_column(table, "user_id")

    op.create_unique_constraint("categories_name_key", "categories", ["name"])
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
