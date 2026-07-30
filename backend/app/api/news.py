import math
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_db, get_current_user
from app.models import NewsItem, NewsCluster
from app.models.news_item import news_item_categories
from app.models.news_cluster import news_cluster_categories
from app.models.user import User
from app.schemas.news_item import NewsItemOut, NewsClusterOut, FeedEntry
from app.schemas.pagination import Page
from app.services.feed_ranking import build_feed

router = APIRouter()


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
    all_entries = build_feed(db, tab, current_user.id, category_ids, source_ids, is_read, read_later, uncategorized)
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
