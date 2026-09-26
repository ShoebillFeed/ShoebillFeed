"""Add api_tokens.scopes

Capability scopes limiting what one API token may do; see
services/token_scopes.py. NULL means unrestricted, so every token that
existed before this migration keeps working exactly as it did.

Revision ID: 0057_add_api_token_scopes
Revises: 0056_add_source_keywords
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0057_add_api_token_scopes"
down_revision = "0056_add_source_keywords"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_tokens",
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("api_tokens", "scopes")
