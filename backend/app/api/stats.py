import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, select, func, cast, Date
from sqlalchemy.orm import Session, selectinload, joinedload, load_only

from app.api.deps import get_db, get_current_user
from app.models import NewsItem, Category, Source, NewsCluster, PodcastShow, PodcastEpisode
from app.models.category_keyword_weight import CategoryKeywordWeight
from app.models.category_weight_snapshot import CategoryWeightSnapshot
from app.models.keyword_cluster import KeywordCluster
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
            func.sum(cast(NewsItem.is_relevant, Integer)).label("relevant"),
            func.sum(cast(NewsItem.is_disliked, Integer)).label("disliked"),
        )
        .where(NewsItem.user_id == current_user.id, NewsItem.fetched_at >= since)
        .group_by(cast(NewsItem.fetched_at, Date))
        .order_by(cast(NewsItem.fetched_at, Date))
    ).all()

    seen_rows = db.execute(
        select(
            cast(NewsItem.last_shown_at, Date).label("date"),
            func.count().label("seen"),
        )
        .where(
            NewsItem.user_id == current_user.id,
            NewsItem.last_shown_at.isnot(None),
            NewsItem.last_shown_at >= since,
        )
        .group_by(cast(NewsItem.last_shown_at, Date))
    ).all()

    seen_by_date = {str(r.date): r.seen for r in seen_rows}

    return [
        {
            "date": str(r.date),
            "fetched": r.fetched,
            "seen": seen_by_date.get(str(r.date), 0),
            "read": int(r.read or 0),
            "relevant": int(r.relevant or 0),
            "disliked": int(r.disliked or 0),
        }
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


@router.get("/keyword-cluster-map")
def keyword_cluster_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top 35 keyword clusters by size with their top keywords and weights."""
    categories = db.scalars(
        select(Category).where(Category.user_id == current_user.id)
    ).all()
    cat_map = {c.id: {"name": c.name, "color": c.color} for c in categories}

    cluster_rows = db.execute(
        select(
            KeywordCluster.category_id,
            KeywordCluster.cluster_index,
            KeywordCluster.cluster_label,
            KeywordCluster.keyword,
            KeywordCluster.score,
            KeywordCluster.cluster_size,
        )
        .where(KeywordCluster.user_id == current_user.id)
        .order_by(KeywordCluster.cluster_size.desc(), KeywordCluster.category_id, KeywordCluster.cluster_index, KeywordCluster.score.desc())
    ).all()

    ckw_map: dict[tuple, float] = {
        (r.category_id, r.keyword): r.weight
        for r in db.scalars(
            select(CategoryKeywordWeight).where(CategoryKeywordWeight.user_id == current_user.id)
        ).all()
    }

    clusters: dict[tuple, dict] = {}
    cluster_order: list[tuple] = []
    for row in cluster_rows:
        key = (row.category_id, row.cluster_index)
        if key not in clusters:
            clusters[key] = {
                "category_name": cat_map.get(row.category_id, {}).get("name", ""),
                "category_color": cat_map.get(row.category_id, {}).get("color", "#6366f1"),
                "cluster_size": row.cluster_size,
                "cluster_label": row.cluster_label or "",
                "keywords": [],
            }
            cluster_order.append(key)
        clusters[key]["keywords"].append({
            "keyword": row.keyword,
            "score": round(row.score, 4),
            "weight": round(ckw_map.get((row.category_id, row.keyword), 1.0), 4),
        })

    sorted_clusters = sorted(cluster_order, key=lambda k: clusters[k]["cluster_size"], reverse=True)[:35]

    result = []
    for key in sorted_clusters:
        c = clusters[key]
        # Fall back to top TF-IDF keyword if LLM label is absent
        if not c["cluster_label"] and c["keywords"]:
            c["cluster_label"] = c["keywords"][0]["keyword"]
        result.append(c)

    return result


@router.post("/refresh-clusters")
def refresh_clusters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger an immediate keyword cluster refresh for the current user."""
    from app.tasks.process_tasks import refresh_keyword_clusters
    refresh_keyword_clusters.apply_async(queue="default")
    return {"status": "queued"}


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


_TOP_N_PER_EPISODE = 8


@router.get("/podcast-episodes")
def podcast_episode_stats(
    show_id: uuid.UUID = Query(...),
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-episode category/keyword/source breakdown for a podcast show, for
    the "which topics has this show actually been covering" chart. Only
    ready episodes have news_item_ids/news_cluster_ids populated (see
    tasks/podcast_tasks.py::_run_generation), so pending/failed episodes are
    excluded rather than showing up as empty bars."""
    show = db.scalar(
        select(PodcastShow).where(PodcastShow.id == show_id, PodcastShow.user_id == current_user.id)
    )
    if not show:
        raise HTTPException(status_code=404, detail="Podcast show not found")

    episodes = db.scalars(
        select(PodcastEpisode)
        .where(PodcastEpisode.show_id == show_id, PodcastEpisode.status == "ready")
        .order_by(PodcastEpisode.created_at.desc())
        .limit(limit)
    ).all()
    episodes = list(reversed(episodes))  # oldest -> newest, left-to-right like the other charts

    all_item_ids: set[uuid.UUID] = set()
    all_cluster_ids: set[uuid.UUID] = set()
    for ep in episodes:
        all_item_ids.update(ep.news_item_ids)
        all_cluster_ids.update(ep.news_cluster_ids)

    # load_only() below matters more than usual here: NewsItem carries a
    # 768-dim pgvector embedding plus raw_content/abstract, none of which
    # this endpoint touches (only extracted_keywords, categories, and
    # source.name are used) -- pulling full rows for every item/cluster
    # referenced across up to `limit` episodes measurably slowed this page.
    items_by_id: dict[uuid.UUID, NewsItem] = {}
    if all_item_ids:
        items = db.scalars(
            select(NewsItem)
            .where(NewsItem.id.in_(all_item_ids))
            .options(
                load_only(NewsItem.extracted_keywords),
                selectinload(NewsItem.categories),
                joinedload(NewsItem.source),
            )
        ).unique().all()
        items_by_id = {i.id: i for i in items}

    clusters_by_id: dict[uuid.UUID, NewsCluster] = {}
    if all_cluster_ids:
        clusters = db.scalars(
            select(NewsCluster)
            .where(NewsCluster.id.in_(all_cluster_ids))
            .options(
                load_only(NewsCluster.extracted_keywords),
                selectinload(NewsCluster.categories),
                # Member items are only used for their source name -- the
                # same load_only reasoning applies, and a single
                # well-covered story's cluster can easily have 8-10 member
                # items, multiplying the wasted cost.
                selectinload(NewsCluster.items).options(
                    load_only(NewsItem.id),
                    joinedload(NewsItem.source),
                ),
            )
        ).unique().all()
        clusters_by_id = {c.id: c for c in clusters}

    result = []
    for ep in episodes:
        cat_counts: dict[uuid.UUID, dict] = {}
        keyword_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}

        def _tally_categories(categories):
            for cat in categories:
                entry = cat_counts.setdefault(
                    cat.id, {"id": str(cat.id), "name": cat.name, "color": cat.color, "count": 0}
                )
                entry["count"] += 1

        def _tally_keywords(keywords):
            for kw in (keywords or []):
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

        for item_id in ep.news_item_ids:
            item = items_by_id.get(item_id)
            if not item:
                continue
            _tally_categories(item.categories)
            _tally_keywords(item.extracted_keywords)
            if item.source:
                source_counts[item.source.name] = source_counts.get(item.source.name, 0) + 1

        for cluster_id in ep.news_cluster_ids:
            cluster = clusters_by_id.get(cluster_id)
            if not cluster:
                continue
            _tally_categories(cluster.categories)
            _tally_keywords(cluster.extracted_keywords)
            # Distinct outlets per cluster (not one count per member item) --
            # a single popular story with a dozen member items shouldn't let
            # one outlet dominate the episode's source tally just because it
            # published early duplicates.
            for name in sorted({item.source.name for item in cluster.items if item.source}):
                source_counts[name] = source_counts.get(name, 0) + 1

        result.append({
            "id": str(ep.id),
            "generated_at": (ep.generated_at or ep.created_at).isoformat(),
            "total_stories": len(ep.news_item_ids) + len(ep.news_cluster_ids),
            "categories": sorted(cat_counts.values(), key=lambda c: -c["count"]),
            "top_keywords": [
                {"keyword": k, "count": c}
                for k, c in sorted(keyword_counts.items(), key=lambda x: -x[1])[:_TOP_N_PER_EPISODE]
            ],
            "top_sources": [
                {"name": n, "count": c}
                for n, c in sorted(source_counts.items(), key=lambda x: -x[1])[:_TOP_N_PER_EPISODE]
            ],
        })

    return result
