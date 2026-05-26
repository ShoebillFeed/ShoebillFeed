import math
import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import NewsItem, CategoryWeight, KeywordWeight, Category
from app.models.category_weight_snapshot import CategoryWeightSnapshot
from app.models.news_item import news_item_categories
from app.models.user_settings import UserSettings


def update_category_weight(
    db: Session,
    category_id: uuid.UUID,
    base: float = 1.0,
    multiplier: float = 0.5,
) -> None:
    total = db.scalar(
        select(func.count()).select_from(NewsItem)
        .join(news_item_categories, news_item_categories.c.news_item_id == NewsItem.id)
        .where(
            news_item_categories.c.category_id == category_id,
            NewsItem.is_relevant == True,  # noqa: E712
        )
    ) or 0

    new_weight = base + math.log1p(total) * multiplier

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
    db.flush()

    category = db.get(Category, category_id)
    if category and category.user_id:
        user_settings = db.scalar(select(UserSettings).where(UserSettings.user_id == category.user_id))
        if not user_settings or user_settings.stats_enabled:
            db.add(CategoryWeightSnapshot(
                category_id=category_id,
                user_id=category.user_id,
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
