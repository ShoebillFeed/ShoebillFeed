import math
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models import NewsItem, CategoryWeight, KeywordWeight, Category
from app.models.category_keyword_weight import CategoryKeywordWeight
from app.models.category_weight_snapshot import CategoryWeightSnapshot
from app.models.news_item import news_item_categories
from app.models.user_settings import UserSettings
from app.services.normalization import normalize_keyword


def update_category_weight(
    db: Session,
    category_id: uuid.UUID,
    base: float = 1.0,
    multiplier: float = 0.5,
    window_days: int = 0,
    ignore_penalty: float = 0.0,
) -> None:
    cutoff = None
    if window_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    def _apply_window(q):
        if cutoff is not None:
            return q.where(or_(NewsItem.published_at >= cutoff, NewsItem.published_at.is_(None)))
        return q

    q_starred = _apply_window(
        select(func.count()).select_from(NewsItem)
        .join(news_item_categories, news_item_categories.c.news_item_id == NewsItem.id)
        .where(
            news_item_categories.c.category_id == category_id,
            NewsItem.is_relevant == True,  # noqa: E712
        )
    )
    total = db.scalar(q_starred) or 0

    total_ignored = 0
    if ignore_penalty > 0:
        q_ignored = _apply_window(
            select(func.count()).select_from(NewsItem)
            .join(news_item_categories, news_item_categories.c.news_item_id == NewsItem.id)
            .where(
                news_item_categories.c.category_id == category_id,
                NewsItem.show_count > 0,
                NewsItem.is_read == False,  # noqa: E712
                NewsItem.is_relevant == False,  # noqa: E712
            )
        )
        total_ignored = db.scalar(q_ignored) or 0

    new_weight = max(0.0, base + math.log1p(total) * multiplier - math.log1p(total_ignored) * ignore_penalty)

    existing = db.scalar(
        select(CategoryWeight).where(CategoryWeight.category_id == category_id)
    )
    category = db.get(Category, category_id)
    if existing:
        existing.weight = new_weight
        existing.total_marked = total
    else:
        db.add(CategoryWeight(
            category_id=category_id,
            user_id=category.user_id if category else None,
            weight=new_weight,
            total_marked=total,
        ))
    db.flush()

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
    seen: set[str] = set()
    for keyword in keywords:
        norm = normalize_keyword(keyword)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        kw = db.get(KeywordWeight, (user_id, norm))
        if kw:
            kw.total_marked += 1
            kw.weight = 1.0 + math.log1p(kw.total_marked) * 0.5
        else:
            db.add(KeywordWeight(user_id=user_id, keyword=norm, weight=1.0 + math.log1p(1) * 0.5, total_marked=1))
    if keywords:
        db.commit()


def apply_keyword_penalty(db: Session, keywords: list[str], user_id, decay: float = 0.8) -> None:
    """Reduce keyword weights for disliked content (multiplicative, floor 0.1)."""
    seen: set[str] = set()
    for keyword in keywords:
        norm = normalize_keyword(keyword)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        kw = db.get(KeywordWeight, (user_id, norm))
        if kw:
            kw.weight = max(0.1, kw.weight * decay)
    if keywords:
        db.commit()


def update_category_keyword_weights(
    db: Session,
    keywords: list[str],
    category_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Increment per-category keyword counts and recompute weights when an article is starred."""
    seen: set[str] = set()
    for keyword in keywords:
        norm = normalize_keyword(keyword)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        ckw = db.get(CategoryKeywordWeight, (user_id, category_id, norm))
        if ckw:
            ckw.starred_count += 1
            ckw.weight = 1.0 + math.log1p(ckw.starred_count) * 0.5
        else:
            db.add(CategoryKeywordWeight(
                user_id=user_id,
                category_id=category_id,
                keyword=norm,
                starred_count=1,
                weight=1.0 + math.log1p(1) * 0.5,
            ))
    if keywords:
        db.flush()


def decay_learned_weights(db: Session, user_factors: dict) -> dict:
    """
    Apply per-user multiplicative decay to all learned keyword/category weights.
    user_factors: {user_id: daily_factor} — users absent or with factor >= 1.0 are skipped.
    Returns counts of rows touched/pruned.
    """
    pruned_kw = decayed_kw = 0
    pruned_ckw = decayed_ckw = 0
    decayed_cat = 0

    # --- Global keyword weights ---
    for kw in db.scalars(select(KeywordWeight).execution_options(yield_per=500)):
        factor = user_factors.get(kw.user_id, 1.0)
        if factor >= 1.0:
            continue
        new_w = max(1.0, kw.weight * factor)
        if new_w <= 1.001:
            db.delete(kw)
            pruned_kw += 1
        else:
            kw.weight = new_w
            decayed_kw += 1

    # --- Per-category keyword weights ---
    for ckw in db.scalars(select(CategoryKeywordWeight).execution_options(yield_per=500)):
        factor = user_factors.get(ckw.user_id, 1.0)
        if factor >= 1.0:
            continue
        new_w = max(1.0, ckw.weight * factor)
        if new_w <= 1.001:
            db.delete(ckw)
            pruned_ckw += 1
        else:
            ckw.weight = new_w
            decayed_ckw += 1

    # --- Category weights (passive; overwritten on next like/read) ---
    for cw in db.scalars(select(CategoryWeight).where(CategoryWeight.user_id != None).execution_options(yield_per=500)):  # noqa: E711
        factor = user_factors.get(cw.user_id, 1.0)
        if factor >= 1.0:
            continue
        cw.weight = max(0.0, cw.weight * factor)
        decayed_cat += 1

    db.commit()
    return {
        "decayed_keywords": decayed_kw,
        "pruned_keywords": pruned_kw,
        "decayed_cat_keywords": decayed_ckw,
        "pruned_cat_keywords": pruned_ckw,
        "decayed_categories": decayed_cat,
    }
