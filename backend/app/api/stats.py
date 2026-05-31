import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, select, func, cast, Date
from sqlalchemy.orm import Session, selectinload, joinedload

from app.api.deps import get_db, get_current_user
from app.models import NewsItem, Category, Source, NewsCluster
from app.models.category_weight_snapshot import CategoryWeightSnapshot
from app.models.news_item import news_item_categories
from app.models.user import User

router = APIRouter()


def _since(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


@router.get("/activity")
def activity(
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily counts of fetched / read / starred articles."""
    since = _since(days)

    rows = db.execute(
        select(
            cast(NewsItem.fetched_at, Date).label("date"),
            func.count().label("fetched"),
            func.sum(cast(NewsItem.is_read, Integer)).label("read"),
            func.sum(cast(NewsItem.is_relevant, Integer)).label("starred"),
        )
        .where(NewsItem.user_id == current_user.id, NewsItem.fetched_at >= since)
        .group_by(cast(NewsItem.fetched_at, Date))
        .order_by(cast(NewsItem.fetched_at, Date))
    ).all()

    return [
        {"date": str(r.date), "fetched": r.fetched, "read": int(r.read or 0), "starred": int(r.starred or 0)}
        for r in rows
    ]


@router.get("/by-category")
def by_category(
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Article counts per category for the given window."""
    since = _since(days)

    rows = db.execute(
        select(
            Category.id,
            Category.name,
            Category.color,
            func.count(NewsItem.id).label("count"),
        )
        .join(news_item_categories, news_item_categories.c.category_id == Category.id)
        .join(NewsItem, NewsItem.id == news_item_categories.c.news_item_id)
        .where(Category.user_id == current_user.id, NewsItem.fetched_at >= since)
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.count(NewsItem.id).desc())
    ).all()

    result = [{"id": str(r.id), "name": r.name, "color": r.color, "count": r.count} for r in rows]

    uncategorized = db.scalar(
        select(func.count(NewsItem.id))
        .where(
            NewsItem.user_id == current_user.id,
            NewsItem.fetched_at >= since,
            ~select(news_item_categories.c.news_item_id)
            .where(news_item_categories.c.news_item_id == NewsItem.id)
            .exists(),
        )
    ) or 0

    if uncategorized:
        result.append({"id": "uncategorized", "name": "Uncategorized", "color": "#9ca3af", "count": uncategorized})

    return result


@router.get("/by-source")
def by_source(
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Article counts per source with per-category breakdown."""
    since = _since(days)

    # Total articles per source (drives sort order)
    total_rows = db.execute(
        select(
            Source.id,
            Source.name,
            Source.source_type,
            func.count(NewsItem.id).label("total"),
        )
        .join(NewsItem, NewsItem.source_id == Source.id)
        .where(Source.user_id == current_user.id, NewsItem.fetched_at >= since)
        .group_by(Source.id, Source.name, Source.source_type)
        .order_by(func.count(NewsItem.id).desc())
    ).all()

    source_map = {
        str(r.id): {
            "id": str(r.id),
            "name": r.name,
            "source_type": r.source_type,
            "total": r.total,
            "categories": [],
        }
        for r in total_rows
    }
    source_order = [str(r.id) for r in total_rows]

    # Per-(source, category) counts
    cat_rows = db.execute(
        select(
            Source.id.label("source_id"),
            Category.id.label("cat_id"),
            Category.name.label("cat_name"),
            Category.color.label("cat_color"),
            func.count(NewsItem.id).label("count"),
        )
        .join(NewsItem, NewsItem.source_id == Source.id)
        .join(news_item_categories, news_item_categories.c.news_item_id == NewsItem.id)
        .join(Category, Category.id == news_item_categories.c.category_id)
        .where(Source.user_id == current_user.id, NewsItem.fetched_at >= since)
        .group_by(Source.id, Category.id, Category.name, Category.color)
    ).all()

    for r in cat_rows:
        sid = str(r.source_id)
        if sid in source_map:
            source_map[sid]["categories"].append({
                "id": str(r.cat_id),
                "name": r.cat_name,
                "color": r.cat_color,
                "count": r.count,
            })

    # Uncategorized articles per source
    uncat_rows = db.execute(
        select(
            Source.id.label("source_id"),
            func.count(NewsItem.id).label("count"),
        )
        .join(NewsItem, NewsItem.source_id == Source.id)
        .where(
            Source.user_id == current_user.id,
            NewsItem.fetched_at >= since,
            ~select(news_item_categories.c.news_item_id)
            .where(news_item_categories.c.news_item_id == NewsItem.id)
            .exists(),
        )
        .group_by(Source.id)
    ).all()

    for r in uncat_rows:
        sid = str(r.source_id)
        if sid in source_map and r.count:
            source_map[sid]["categories"].append({
                "id": "uncategorized",
                "name": "Uncategorized",
                "color": "#9ca3af",
                "count": r.count,
            })

    return [source_map[sid] for sid in source_order]


@router.get("/weight-history")
def weight_history(
    days: Annotated[int, Query(ge=1, le=365)] = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Learned-weight snapshots per category over time."""
    since = _since(days)

    categories = db.scalars(
        select(Category).where(Category.user_id == current_user.id)
    ).all()
    cat_map = {c.id: {"id": str(c.id), "name": c.name, "color": c.color} for c in categories}

    snapshots = db.execute(
        select(
            CategoryWeightSnapshot.category_id,
            CategoryWeightSnapshot.weight,
            CategoryWeightSnapshot.total_marked,
            CategoryWeightSnapshot.recorded_at,
        )
        .where(
            CategoryWeightSnapshot.user_id == current_user.id,
            CategoryWeightSnapshot.recorded_at >= since,
        )
        .order_by(CategoryWeightSnapshot.category_id, CategoryWeightSnapshot.recorded_at)
    ).all()

    by_cat: dict[str, list] = {}
    for row in snapshots:
        cid = str(row.category_id)
        if cid not in by_cat:
            by_cat[cid] = []
        by_cat[cid].append({
            "date": row.recorded_at.isoformat(),
            "weight": round(row.weight, 4),
            "total_marked": row.total_marked,
        })

    result = []
    for cid, meta in cat_map.items():
        key = str(cid)
        if key in by_cat:
            result.append({**meta, "snapshots": by_cat[key]})

    return result


@router.get("/source-clusters")
def source_clusters(
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Which source pairs appear together in clusters most often, grouped by category."""
    since = _since(days)

    clusters = db.scalars(
        select(NewsCluster)
        .where(NewsCluster.user_id == current_user.id, NewsCluster.created_at >= since)
        .options(
            selectinload(NewsCluster.items).joinedload(NewsItem.source),
            selectinload(NewsCluster.categories),
        )
    ).unique().all()

    pair_totals: dict[tuple[str, str], int] = {}
    pair_cats: dict[tuple[str, str], dict[str, int]] = {}
    source_meta: dict[str, dict] = {}
    cat_colors: dict[str, str] = {}

    for cluster in clusters:
        sources: dict[str, object] = {}
        for item in cluster.items:
            if item.source_id and item.source:
                sid = str(item.source_id)
                sources[sid] = item.source
                source_meta[sid] = {
                    "id": sid,
                    "name": item.source.name,
                    "source_type": item.source.source_type,
                }
        sids = sorted(sources)
        if len(sids) < 2:
            continue

        for cat in cluster.categories:
            cat_colors[cat.name] = cat.color

        for i in range(len(sids)):
            for j in range(i + 1, len(sids)):
                key = (sids[i], sids[j])
                pair_totals[key] = pair_totals.get(key, 0) + 1
                cats = pair_cats.setdefault(key, {})
                for cat in cluster.categories:
                    cats[cat.name] = cats.get(cat.name, 0) + 1
                if not cluster.categories:
                    cats["Uncategorized"] = cats.get("Uncategorized", 0) + 1

    result = []
    for key in sorted(pair_totals, key=pair_totals.__getitem__, reverse=True)[:15]:
        sid_a, sid_b = key
        if sid_a not in source_meta or sid_b not in source_meta:
            continue
        cats = pair_cats.get(key, {})
        result.append({
            "source_a": source_meta[sid_a],
            "source_b": source_meta[sid_b],
            "total": pair_totals[key],
            "categories": [
                {"name": n, "count": c, "color": cat_colors.get(n, "#9ca3af")}
                for n, c in sorted(cats.items(), key=lambda x: -x[1])
            ],
        })

    return result
