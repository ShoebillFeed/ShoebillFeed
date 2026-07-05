import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_db, get_current_user
from app.models import NewsItem, Category, CategoryWeight, KeywordWeight, NewsCluster
from app.models.category_keyword_weight import CategoryKeywordWeight
from app.models.keyword_cluster import KeywordCluster
from app.models.news_item import news_item_categories
from app.models.news_cluster import news_cluster_categories
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.news_item import NewsItemOut, NewsClusterOut, FeedEntry
from app.schemas.pagination import Page
from app.services.normalization import normalize_keyword

router = APIRouter()

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _entry_source_ids(entry) -> set:
    """Collect all source IDs from an entry (item or cluster)."""
    if isinstance(entry, NewsItem):
        return {entry.source_id} if entry.source_id else set()
    return {item.source_id for item in entry.items if item.source_id}


def _apply_diversity(
    sorted_entries: list,
    learned_weights: dict,
    max_per_cat: int,
    max_per_src: int,
    explore_frac: float,
) -> list:
    """
    Post-sort diversity pass applied to the Relevant and Impact tabs.

    1. Splits entries into a high-interest pool (at least one category with a
       learned weight > 1) and an explore pool (all categories at baseline).
    2. Applies per-category and per-source caps to each pool, deferring excess
       entries to later positions rather than dropping them.
    3. Interleaves explore items into the main sequence at the configured
       fraction so discovery content is spread throughout the feed.
    """
    def is_high(entry) -> bool:
        return any(learned_weights.get(c.id, 1.0) > 1.001 for c in entry.categories)

    high = [e for e in sorted_entries if is_high(e)]
    low  = [e for e in sorted_entries if not is_high(e)]

    def apply_caps(pool: list) -> list:
        if not max_per_cat and not max_per_src:
            return pool
        result: list = []
        deferred: list = []
        cat_count: dict = {}
        src_count: dict = {}
        for entry in pool:
            cat_ids = [c.id for c in entry.categories]
            src_ids = _entry_source_ids(entry)
            over_cat = max_per_cat > 0 and any(cat_count.get(c, 0) >= max_per_cat for c in cat_ids)
            over_src = max_per_src > 0 and any(src_count.get(s, 0) >= max_per_src for s in src_ids)
            if over_cat or over_src:
                deferred.append(entry)
            else:
                result.append(entry)
                for c in cat_ids:
                    cat_count[c] = cat_count.get(c, 0) + 1
                for s in src_ids:
                    src_count[s] = src_count.get(s, 0) + 1
        result.extend(deferred)
        return result

    high = apply_caps(high)
    low  = apply_caps(low)

    if explore_frac <= 0 or not low:
        return high + low

    # Insert 1 explore item every `interval` main items
    interval = max(1, round((1.0 - explore_frac) / explore_frac))
    result: list = []
    lo_idx = 0
    for i, item in enumerate(high):
        result.append(item)
        if lo_idx < len(low) and (i + 1) % interval == 0:
            result.append(low[lo_idx])
            lo_idx += 1
    result.extend(low[lo_idx:])
    return result


def _age_days(entry) -> float:
    """Return the age of an entry in fractional days (0 = just published)."""
    now = datetime.now(timezone.utc)
    if isinstance(entry, NewsItem):
        dt = entry.published_at or entry.fetched_at
    else:
        dt = entry.published_at or entry.created_at
    if not dt:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (now - dt).total_seconds() / 86400.0)


def _time_decay(entry, param: float) -> float:
    """1 / (0.5 * (age_days * param + 2))  — equals 1.0 when age=0."""
    if param <= 0:
        return 1.0
    return 1.0 / (0.5 * (_age_days(entry) * param + 2.0))


def _show_again_decay(entry, param: float) -> float:
    """Cumulative penalty per showing: 1 / (1 + show_count * param).
    param=0 → disabled. Clusters with new items since last shown reset to 1.0."""
    if param <= 0:
        return 1.0
    count = getattr(entry, 'show_count', 0) or 0
    if count == 0:
        return 1.0
    if isinstance(entry, NewsCluster) and entry.last_shown_at is not None:
        lst = entry.last_shown_at
        if lst.tzinfo is None:
            lst = lst.replace(tzinfo=timezone.utc)
        for item in entry.items:
            ft = item.fetched_at
            if ft.tzinfo is None:
                ft = ft.replace(tzinfo=timezone.utc)
            if ft > lst:
                return 1.0  # new items arrived — treat as never shown
    return 1.0 / (1.0 + count * param)


def _sort_key_newest(entry):
    dt = entry.published_at if isinstance(entry, NewsItem) else (entry.published_at or entry.created_at)
    fallback = entry.fetched_at if isinstance(entry, NewsItem) else entry.created_at
    return dt or fallback


def _build_feed(
    db: Session,
    tab: str,
    user_id: uuid.UUID,
    category_ids: list[uuid.UUID],
    source_ids: list[uuid.UUID],
    is_read: bool | None,
    read_later: bool | None,
    uncategorized: bool | None = None,
) -> list:
    item_q = (
        select(NewsItem)
        .where(NewsItem.cluster_id == None, NewsItem.user_id == user_id)  # noqa: E711
        .options(joinedload(NewsItem.source), selectinload(NewsItem.categories))
    )
    _has_items = (
        select(NewsItem.id).where(NewsItem.cluster_id == NewsCluster.id).exists()
    )
    cluster_q = (
        select(NewsCluster)
        .where(_has_items, NewsCluster.user_id == user_id)
        .options(
            joinedload(NewsCluster.items).joinedload(NewsItem.source),
            selectinload(NewsCluster.categories),
        )
    )

    if category_ids:
        item_q = item_q.where(
            select(news_item_categories.c.news_item_id)
            .where(
                news_item_categories.c.news_item_id == NewsItem.id,
                news_item_categories.c.category_id.in_(category_ids),
            )
            .exists()
        )
        cluster_q = cluster_q.where(
            select(news_cluster_categories.c.news_cluster_id)
            .where(
                news_cluster_categories.c.news_cluster_id == NewsCluster.id,
                news_cluster_categories.c.category_id.in_(category_ids),
            )
            .exists()
        )
    if source_ids:
        item_q = item_q.where(NewsItem.source_id.in_(source_ids))
        cluster_q = cluster_q.where(
            select(NewsItem.id)
            .where(NewsItem.cluster_id == NewsCluster.id, NewsItem.source_id.in_(source_ids))
            .exists()
        )
    if is_read is not None:
        item_q = item_q.where(NewsItem.is_read == is_read)
        cluster_q = cluster_q.where(NewsCluster.is_read == is_read)
    if read_later is not None:
        item_q = item_q.where(NewsItem.read_later == read_later)
        cluster_q = cluster_q.where(NewsCluster.read_later == read_later)
    if uncategorized:
        item_q = item_q.where(
            ~select(news_item_categories.c.news_item_id)
            .where(news_item_categories.c.news_item_id == NewsItem.id)
            .exists()
        )
        cluster_q = cluster_q.where(
            ~select(news_cluster_categories.c.news_cluster_id)
            .where(news_cluster_categories.c.news_cluster_id == NewsCluster.id)
            .exists()
        )

    user_settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))

    # Bound the candidate set for the relevant tab to prevent unbounded growth
    if tab == "relevant":
        window = (user_settings.learning_window_days if user_settings else 90) or 180
        cutoff = datetime.now(timezone.utc) - timedelta(days=window)
        item_q = item_q.where(
            (NewsItem.published_at >= cutoff) | (NewsItem.read_later == True) | (NewsItem.is_relevant == True)  # noqa: E712
        )
        cluster_q = cluster_q.where(
            (NewsCluster.published_at >= cutoff) | (NewsCluster.read_later == True) | (NewsCluster.is_relevant == True)  # noqa: E712
        )

    _LIMIT = 2000
    if tab == "newest":
        item_q = item_q.order_by(NewsItem.published_at.desc()).limit(_LIMIT)
        cluster_q = cluster_q.order_by(NewsCluster.published_at.desc()).limit(_LIMIT)
    else:
        item_q = item_q.limit(_LIMIT)
        cluster_q = cluster_q.limit(_LIMIT)

    standalone = list(db.scalars(item_q).unique().all())
    clusters = list(db.scalars(cluster_q).unique().all())
    all_entries = standalone + clusters

    decay_param = user_settings.time_decay_param if user_settings else 2.0
    show_decay = user_settings.show_decay_param if user_settings else 0.0

    if tab == "newest":
        all_entries.sort(key=_sort_key_newest, reverse=True)
    elif tab == "relevant":
        cat_weights = {
            cw.category_id: cw.weight * cw.manual_weight
            for cw in db.scalars(select(CategoryWeight).where(CategoryWeight.user_id == user_id)).all()
        }
        # Global keyword weights (legacy signal, kept as a floor)
        kw_weights = {
            kw.keyword: kw.weight
            for kw in db.scalars(select(KeywordWeight).where(KeywordWeight.user_id == user_id)).all()
        }
        # Per-category keyword weights: {(category_id, keyword): weight}
        cat_kw_weights: dict[tuple, float] = {
            (ckw.category_id, ckw.keyword): ckw.weight
            for ckw in db.scalars(
                select(CategoryKeywordWeight).where(CategoryKeywordWeight.user_id == user_id)
            ).all()
        }
        # Keyword cluster lookup: {(category_id, keyword): cluster_index}
        cluster_lookup: dict[tuple, int] = {}
        # Cluster synonym weight: {(category_id, cluster_index): max per-cat keyword weight in cluster}
        cluster_max_weight: dict[tuple, float] = {}
        for kc in db.scalars(select(KeywordCluster).where(KeywordCluster.user_id == user_id)).all():
            cluster_lookup[(kc.category_id, kc.keyword)] = kc.cluster_index
            key = (kc.category_id, kc.cluster_index)
            existing = cluster_max_weight.get(key, 1.0)
            per_cat = cat_kw_weights.get((kc.category_id, kc.keyword), 1.0)
            cluster_max_weight[key] = max(existing, per_cat)

        learn_w = user_settings.relevance_learning_weight if user_settings else 1.0
        cluster_w = user_settings.relevance_cluster_weight if user_settings else 0.5

        def _rel_key(e):
            cat_ids = [c.id for c in e.categories]
            raw_cat = max((cat_weights.get(cid, 1.0) for cid in cat_ids), default=1.0)
            cat_w = 1.0 + (raw_cat - 1.0) * learn_w

            n = len(e.items) if isinstance(e, NewsCluster) else 1
            source_bonus = 1.0 + math.log1p(n - 1) * cluster_w

            keywords = e.extracted_keywords or []
            if keywords and cat_ids:
                kw_scores = []
                for k in keywords:
                    norm = normalize_keyword(k)
                    # Global weight as baseline
                    w = kw_weights.get(norm, 1.0)
                    for cid in cat_ids:
                        # Per-category direct weight
                        w = max(w, cat_kw_weights.get((cid, norm), 1.0))
                        # Cluster synonym expansion: inherit max weight of cluster peers
                        ci = cluster_lookup.get((cid, norm))
                        if ci is not None:
                            w = max(w, cluster_max_weight.get((cid, ci), 1.0))
                    kw_scores.append(w)
                raw_kw = sum(kw_scores) / len(kw_scores)
            else:
                raw_kw = 1.0
            kw_factor = 1.0 + (raw_kw - 1.0) * learn_w

            return cat_w * source_bonus * kw_factor * _time_decay(e, decay_param) * _show_again_decay(e, show_decay)
        all_entries.sort(key=_rel_key, reverse=True)
    elif tab == "impact":
        all_entries.sort(key=lambda e: (e.impact_score or 0) * _time_decay(e, decay_param) * _show_again_decay(e, show_decay), reverse=True)

    # Diversity pass: per-category/source caps + exploration budget (relevant + impact only)
    if tab != "newest":
        max_per_cat = (user_settings.max_per_category if user_settings else 0) or 0
        max_per_src = (user_settings.max_per_source if user_settings else 0) or 0
        explore_frac = (user_settings.exploration_fraction if user_settings else 0.0) or 0.0
        if max_per_cat or max_per_src or explore_frac > 0:
            learned_weights = {
                cw.category_id: cw.weight
                for cw in db.scalars(select(CategoryWeight).where(CategoryWeight.user_id == user_id)).all()
            }
            all_entries = _apply_diversity(all_entries, learned_weights, max_per_cat, max_per_src, explore_frac)

    return all_entries


@router.get("", response_model=Page[FeedEntry])
def list_news(
    tab: Literal["newest", "relevant", "impact"] = "newest",
    category_ids: list[uuid.UUID] = Query(default=[]),
    source_ids: list[uuid.UUID] = Query(default=[]),
    is_read: bool | None = None,
    read_later: bool | None = None,
    uncategorized: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_entries = _build_feed(db, tab, current_user.id, category_ids, source_ids, is_read, read_later, uncategorized)
    total = len(all_entries)
    page_entries = all_entries[(page - 1) * page_size: page * page_size]

    items_out: list[FeedEntry] = []
    for entry in page_entries:
        if isinstance(entry, NewsItem):
            items_out.append(NewsItemOut.model_validate(entry))
        else:
            items_out.append(NewsClusterOut.model_validate(entry))

    return Page(
        items=items_out,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 1,
    )


def _get_item(item_id: uuid.UUID, db: Session, user_id: uuid.UUID) -> NewsItem:
    item = db.scalar(
        select(NewsItem)
        .options(selectinload(NewsItem.categories))
        .where(NewsItem.id == item_id, NewsItem.user_id == user_id)
    )
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    return item


@router.get("/search", response_model=list[NewsItemOut])
def search_news(
    q: str = Query(..., min_length=1),
    sort: Literal["newest", "relevant", "impact"] = Query("newest"),
    category_ids: list[uuid.UUID] = Query(default=[]),
    source_ids: list[uuid.UUID] = Query(default=[]),
    is_read: bool | None = Query(default=None),
    read_later: bool | None = Query(default=None),
    page_size: int = Query(50, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import or_
    pattern = f"%{q}%"
    stmt = (
        select(NewsItem)
        .where(
            NewsItem.user_id == current_user.id,
            or_(
                NewsItem.title.ilike(pattern),
                NewsItem.abstract.ilike(pattern),
                NewsItem.raw_content.ilike(pattern),
            ),
        )
        .options(selectinload(NewsItem.categories), selectinload(NewsItem.source))
    )
    if category_ids:
        stmt = stmt.where(
            select(news_item_categories.c.news_item_id)
            .where(
                news_item_categories.c.news_item_id == NewsItem.id,
                news_item_categories.c.category_id.in_(category_ids),
            )
            .exists()
        )
    if source_ids:
        stmt = stmt.where(NewsItem.source_id.in_(source_ids))
    if is_read is not None:
        stmt = stmt.where(NewsItem.is_read == is_read)
    if read_later is not None:
        stmt = stmt.where(NewsItem.read_later == read_later)
    if sort == "relevant":
        stmt = stmt.order_by(NewsItem.relevance_score.desc().nulls_last(), NewsItem.fetched_at.desc())
    elif sort == "impact":
        stmt = stmt.order_by(NewsItem.impact_score.desc().nulls_last(), NewsItem.fetched_at.desc())
    else:
        stmt = stmt.order_by(NewsItem.fetched_at.desc())
    return db.scalars(stmt.limit(page_size)).all()


@router.get("/{item_id}", response_model=NewsItemOut)
def get_news_item(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.scalar(
        select(NewsItem)
        .options(joinedload(NewsItem.source), selectinload(NewsItem.categories))
        .where(NewsItem.id == item_id, NewsItem.user_id == current_user.id)
    )
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    return item


@router.patch("/{item_id}/read", response_model=NewsItemOut)
def toggle_read(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _get_item(item_id, db, current_user.id)
    category_ids = [str(cat.id) for cat in item.categories]
    item.is_read = not item.is_read
    db.commit()
    if category_ids:
        from app.tasks.process_tasks import _recalculate_weights
        _recalculate_weights.apply_async(
            kwargs={"user_id": str(current_user.id), "category_ids": category_ids},
            queue="default",
        )
    db.refresh(item)
    return item


@router.patch("/{item_id}/relevant", response_model=NewsItemOut)
def toggle_relevant(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _get_item(item_id, db, current_user.id)
    category_ids = [str(cat.id) for cat in item.categories]
    item.is_relevant = not item.is_relevant
    is_now_relevant = item.is_relevant
    db.commit()
    if category_ids:
        from app.tasks.process_tasks import _recalculate_weights
        _recalculate_weights.apply_async(
            kwargs={
                "user_id": str(current_user.id),
                "category_ids": category_ids,
                "liked_item_id": str(item.id) if is_now_relevant else None,
            },
            queue="default",
        )
    db.refresh(item)
    return item


@router.patch("/{item_id}/dislike", response_model=NewsItemOut)
def dislike_item(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _get_item(item_id, db, current_user.id)
    was_relevant = item.is_relevant
    category_ids = [str(cat.id) for cat in item.categories] if was_relevant else []
    item.is_read = True
    item.is_relevant = False
    item.is_disliked = True
    db.commit()
    from app.tasks.process_tasks import _recalculate_weights
    _recalculate_weights.apply_async(
        kwargs={
            "user_id": str(current_user.id),
            "category_ids": category_ids,
            "disliked_item_id": str(item.id),
        },
        queue="default",
    )
    db.refresh(item)
    return item


@router.patch("/{item_id}/read-later", response_model=NewsItemOut)
def toggle_read_later(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _get_item(item_id, db, current_user.id)
    item.read_later = not item.read_later
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/reprocess")
def reprocess_item(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _get_item(item_id, db, current_user.id)
    item.llm_processed = False
    db.commit()
    from app.tasks.process_tasks import process_news_item
    process_news_item.apply_async(args=[str(item_id)], queue="process")
    return {"queued": True}


@router.post("/mark-all-read")
def mark_all_read(
    category_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item_q = select(NewsItem).where(
        NewsItem.is_read == False, NewsItem.cluster_id == None, NewsItem.user_id == current_user.id  # noqa: E711,E712
    )
    cluster_q = select(NewsCluster).where(NewsCluster.is_read == False, NewsCluster.user_id == current_user.id)  # noqa: E712
    if category_id:
        item_q = item_q.where(
            select(news_item_categories.c.news_item_id)
            .where(
                news_item_categories.c.news_item_id == NewsItem.id,
                news_item_categories.c.category_id == category_id,
            )
            .exists()
        )
        cluster_q = cluster_q.where(
            select(news_cluster_categories.c.news_cluster_id)
            .where(
                news_cluster_categories.c.news_cluster_id == NewsCluster.id,
                news_cluster_categories.c.category_id == category_id,
            )
            .exists()
        )

    count = 0
    for item in db.scalars(item_q).all():
        item.is_read = True
        count += 1
    for cluster in db.scalars(cluster_q).all():
        cluster.is_read = True
        count += 1
    db.commit()
    return {"updated": count}


class MarkShownPayload(PydanticBaseModel):
    item_ids: list[uuid.UUID] = []
    cluster_ids: list[uuid.UUID] = []


@router.post("/mark-shown")
def mark_shown(
    payload: MarkShownPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    # Collect categories of items being shown for the first time without engagement,
    # so we can apply ignore penalties after the commit.
    penalty_cat_ids: set[uuid.UUID] = set()

    if payload.item_ids:
        for item in db.scalars(
            select(NewsItem)
            .where(NewsItem.id.in_(payload.item_ids), NewsItem.user_id == current_user.id)
            .options(selectinload(NewsItem.categories))
        ).all():
            if item.show_count == 0 and not item.is_read and not item.is_relevant:
                penalty_cat_ids.update(cat.id for cat in item.categories)
            item.show_count = (item.show_count or 0) + 1
            item.last_shown_at = now

    if payload.cluster_ids:
        for cluster in db.scalars(
            select(NewsCluster)
            .where(NewsCluster.id.in_(payload.cluster_ids), NewsCluster.user_id == current_user.id)
            .options(selectinload(NewsCluster.categories))
        ).all():
            if cluster.show_count == 0 and not cluster.is_read and not cluster.is_relevant:
                penalty_cat_ids.update(cat.id for cat in cluster.categories)
            cluster.show_count = (cluster.show_count or 0) + 1
            cluster.last_shown_at = now

    db.commit()

    if penalty_cat_ids:
        from app.tasks.process_tasks import _recalculate_weights
        _recalculate_weights.apply_async(
            kwargs={
                "user_id": str(current_user.id),
                "category_ids": [str(cid) for cid in penalty_cat_ids],
            },
            queue="default",
        )

    return {"updated": len(payload.item_ids) + len(payload.cluster_ids)}


@router.delete("/{item_id}", status_code=204)
def delete_news_item(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _get_item(item_id, db, current_user.id)
    db.delete(item)
    db.commit()
