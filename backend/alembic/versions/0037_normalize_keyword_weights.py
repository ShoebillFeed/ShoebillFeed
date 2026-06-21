"""normalize existing keyword_weights to lemmatized canonical forms

Revision ID: 0037_normalize_keyword_weights
Revises: 0036_push_top_category_percent
Create Date: 2026-06-21

"""
import math
from collections import defaultdict
from alembic import op
from sqlalchemy import text

revision = "0037_normalize_keyword_weights"
down_revision = "0036_push_top_category_percent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.services.normalization import normalize_keyword

    bind = op.get_bind()

    rows = bind.execute(
        text("SELECT user_id, keyword, total_marked FROM keyword_weights")
    ).fetchall()

    if not rows:
        return

    # Group by (user_id, normalized_keyword), summing total_marked for duplicates.
    totals: dict[tuple, int] = defaultdict(int)
    for row in rows:
        norm = normalize_keyword(row.keyword) or row.keyword
        totals[(str(row.user_id), norm)] += row.total_marked

    bind.execute(text("DELETE FROM keyword_weights"))

    for (user_id, keyword), total_marked in totals.items():
        weight = 1.0 + math.log1p(total_marked) * 0.5
        bind.execute(
            text(
                "INSERT INTO keyword_weights (user_id, keyword, weight, total_marked) "
                "VALUES (:user_id, :keyword, :weight, :total_marked)"
            ),
            {"user_id": user_id, "keyword": keyword, "weight": weight, "total_marked": total_marked},
        )


def downgrade() -> None:
    # Normalization is lossy — original surface forms cannot be recovered.
    pass
