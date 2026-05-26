import math
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_db, get_current_user
from app.models import NewsItem, Category, CategoryWeight, KeywordWeight, NewsCluster
from app.models.news_item import news_item_categories
from app.models.news_cluster import news_cluster_categories
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.news_item import NewsItemOut, NewsClusterOut, FeedEntry
from app.schemas.pagination import Page
from app.services.scoring import update_category_weight, update_keyword_weights

router = APIRouter()

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _sort_key_newest(entry):
    dt = entry.published_at if isinstance(entry, NewsItem) else (entry.published_at or entry.created_at)
    fallback = entry.fetched_at if isinstance(entry, NewsItem) else entry.created_at
    return dt or fallback


def _build_feed(
    db: Session,
    tab: str,
    user_id: uuid.UUID,
    category_id: uuid.UUID | None,
    source_id: uuid.UUID | None,
    is_read: bool | None,
    read_later: bool | None,
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
    if source_id:
        item_q = item_q.where(NewsItem.source_id == source_id)
        cluster_q = cluster_q.where(
            select(NewsItem.id)
            .where(NewsItem.cluster_id == NewsCluster.id, NewsItem.source_id == source_id)
            .exists()
        )
    if is_read is not None:
        item_q = item_q.where(NewsItem.is_read == is_read)
        cluster_q = cluster_q.where(NewsCluster.is_read == is_read)
    if read_later is not None:
        item_q = item_q.where(NewsItem.read_later == read_later)
        cluster_q = cluster_q.where(NewsCluster.read_later == read_later)

    standalone = list(db.scalars(item_q).unique().all())
    clusters = list(db.scalars(cluster_q).unique().all())
    all_entries = standalone + clusters

    if tab == "newest":
        all_entries.sort(key=_sort_key_newest, reverse=True)
    elif tab == "relevant":
        cat_weights = {
            cw.category_id: cw.weight * cw.manual_weight
            for cw in db.scalars(select(CategoryWeight)).all()
        }
        kw_weights = {
            kw.keyword: kw.weight
            for kw in db.scalars(select(KeywordWeight).where(KeywordWeight.user_id == user_id)).all()
        }
        user_settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
        llm_w = user_settings.relevance_llm_weight if user_settings else 1.0
        learn_w = user_settings.relevance_learning_weight if user_settings else 1.0
        cluster_w = user_settings.relevance_cluster_weight if user_settings else 0.5

        def _rel_key(e):
            cat_ids = [c.id for c in e.categories]
            raw_cat = max((cat_weights.get(cid, 1.0) for cid in cat_ids), default=1.0)
            # Blend category influence: 0 = flat (1.0), 1 = raw, 2 = amplified
            cat_w = 1.0 + (raw_cat - 1.0) * learn_w

            n = len(e.items) if isinstance(e, NewsCluster) else 1
            source_bonus = 1.0 + math.log1p(n - 1) * cluster_w

            keywords = e.extracted_keywords or []
            raw_kw = (
                sum(kw_weights.get(k, 1.0) for k in keywords) / len(keywords)
                if keywords else 1.0
            )
            kw_factor = 1.0 + (raw_kw - 1.0) * learn_w

            return (e.relevance_score or 5) * llm_w * cat_w * source_bonus * kw_factor
        all_entries.sort(key=_rel_key, reverse=True)
    elif tab == "impact":
        all_entries.sort(key=lambda e: e.impact_score or 0, reverse=True)

    return all_entries


@router.get("", response_model=Page[FeedEntry])
def list_news(
    tab: Literal["newest", "relevant", "impact"] = "newest",
    category_id: uuid.UUID | None = None,
    source_id: uuid.UUID | None = None,
    is_read: bool | None = None,
    read_later: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_entries = _build_feed(db, tab, current_user.id, category_id, source_id, is_read, read_later)
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
    item = db.scalar(select(NewsItem).where(NewsItem.id == item_id, NewsItem.user_id == user_id))
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    return item


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
    item.is_read = not item.is_read
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}/relevant", response_model=NewsItemOut)
def toggle_relevant(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _get_item(item_id, db, current_user.id)
    item.is_relevant = not item.is_relevant
    db.commit()
    if item.is_relevant:
        user_settings = db.scalar(select(UserSettings).where(UserSettings.user_id == current_user.id))
        base = user_settings.weight_base if user_settings else 1.0
        multiplier = user_settings.weight_log_multiplier if user_settings else 0.5
        for cat in item.categories:
            update_category_weight(db, cat.id, base=base, multiplier=multiplier)
        if item.extracted_keywords:
            update_keyword_weights(db, item.extracted_keywords, current_user.id)
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


@router.delete("/{item_id}", status_code=204)
def delete_news_item(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _get_item(item_id, db, current_user.id)
    db.delete(item)
    db.commit()
