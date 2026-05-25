import math
import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import NewsItem, CategoryWeight, KeywordWeight


def update_category_weight(db: Session, category_id: uuid.UUID) -> None:
    total = db.scalar(
        select(func.count()).select_from(NewsItem).where(
            NewsItem.category_id == category_id,
            NewsItem.is_relevant == True,  # noqa: E712
        )
    ) or 0

    new_weight = 1.0 + math.log1p(total) * 0.5

    existing = db.scalar(
        select(CategoryWeight).where(CategoryWeight.category_id == category_id)
    )
    if existing:
        existing.weight = new_weight
        existing.total_marked = total
    else:
        db.add(CategoryWeight(
            category_id=category_id,
            weight=new_weight,
            total_marked=total,
        ))
    db.commit()


def update_keyword_weights(db: Session, keywords: list[str], user_id) -> None:
    for keyword in keywords:
        kw = db.get(KeywordWeight, (user_id, keyword))
        if kw:
            kw.total_marked += 1
            kw.weight = 1.0 + math.log1p(kw.total_marked) * 0.5
        else:
            db.add(KeywordWeight(user_id=user_id, keyword=keyword, weight=1.0 + math.log1p(1) * 0.5, total_marked=1))
    if keywords:
        db.commit()
