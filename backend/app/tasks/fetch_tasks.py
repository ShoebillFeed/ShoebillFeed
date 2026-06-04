import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from hashlib import sha256

from sqlalchemy import select, func, update, exists

from app.database import SessionLocal
from app.models import NewsItem, NewsCluster, Source
from app.models.category import Category
from app.services.deduplication import url_hash, content_hash
from app.services.fetchers.base import get_fetcher, RawNewsItem
from app.services.clustering import cluster_new_items
import app.services.fetchers.rss  # noqa: F401 — register fetchers
import app.services.fetchers.reddit  # noqa: F401
import app.services.fetchers.youtube  # noqa: F401
import app.services.fetchers.email_imap  # noqa: F401
import app.services.fetchers.mastodon  # noqa: F401
import app.services.fetchers.scholar  # noqa: F401
import app.services.fetchers.atom  # noqa: F401
import app.services.fetchers.lemmy  # noqa: F401
import app.services.fetchers.github  # noqa: F401
import app.services.fetchers.bluesky  # noqa: F401
import app.services.fetchers.telegram  # noqa: F401
import app.services.fetchers.scraper  # noqa: F401
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _config_key(source: Source) -> str:
    """Stable hash identifying a unique (source_type, config) combination."""
    payload = json.dumps(source.config, sort_keys=True, ensure_ascii=False)
    return f"{source.source_type}:{sha256(payload.encode()).hexdigest()[:16]}"


def _save_items_for_source(
    db,
    source: Source,
    raw_items: list[RawNewsItem],
) -> list[uuid.UUID]:
    """Persist raw items for a single source/user. Returns IDs of newly created items."""
    new_item_ids: list[uuid.UUID] = []
    new_count = skipped = 0

    for raw in raw_items:
        h = url_hash(raw.url)

        if db.scalar(select(NewsItem.id).where(
            NewsItem.url_hash == h,
            NewsItem.user_id == source.user_id,
        )):
            skipped += 1
            continue

        ch = content_hash(raw.raw_content) if raw.raw_content else None
        if ch and db.scalar(
            select(NewsItem.id).where(
                NewsItem.content_hash == ch,
                NewsItem.source_id == source.id,
            )
        ):
            skipped += 1
            continue

        donor = db.scalar(
            select(NewsItem).where(
                NewsItem.url_hash == h,
                NewsItem.llm_processed == True,  # noqa: E712
                NewsItem.user_id != source.user_id,
            )
        ) if source.user_id else None

        item = NewsItem(
            source_id=source.id,
            user_id=source.user_id,
            title=raw.title,
            url=raw.url,
            url_hash=h,
            content_hash=ch,
            raw_content=raw.raw_content,
            published_at=raw.published_at,
            image_url=donor.image_url if donor and donor.image_url else raw.image_url,
        )

        if donor and donor.abstract:
            item.abstract = donor.abstract
            item.extracted_keywords = donor.extracted_keywords
            item.impact_score = donor.impact_score
            item.llm_processed = True
            if donor.extracted_keywords and source.user_id:
                kw_lower = {k.lower() for k in donor.extracted_keywords}
                user_cats = db.scalars(
                    select(Category).where(
                        Category.user_id == source.user_id,
                        Category.is_active == True,  # noqa: E712
                    )
                ).all()
                item.categories = [
                    cat for cat in user_cats
                    if any(k.lower() in kw_lower for k in cat.keywords)
                ]
            logger.debug("Reused LLM results from donor %s for user %s", donor.id, source.user_id)

        db.add(item)
        db.flush()
        new_item_ids.append(item.id)
        new_count += 1

    logger.info("Source %s (user %s): %d new, %d duplicate", source.name, source.user_id, new_count, skipped)
    return new_item_ids


@celery_app.task(name="app.tasks.fetch_tasks.fetch_source", queue="fetch", bind=True, max_retries=3)
def fetch_source(self, source_id: str, companion_ids: list[str] | None = None) -> dict:
    """Fetch a source once and fan the results out to all companion sources
    (same source_type+config, different users). One HTTP request serves all."""
    from app.tasks.process_tasks import process_news_item, process_cluster

    db = SessionLocal()
    try:
        source = db.get(Source, uuid.UUID(source_id))
        if not source or not source.is_active:
            return {"skipped": True}

        fetcher = get_fetcher(source.source_type, source.config)
        raw_items = fetcher.fetch()
        logger.info("Fetched %d raw items from '%s' (shared across %d source(s))",
                    len(raw_items), source.name, 1 + len(companion_ids or []))

        now = datetime.now(tz=timezone.utc)
        all_new_item_ids: list[uuid.UUID] = []

        # Primary source
        all_new_item_ids.extend(_save_items_for_source(db, source, raw_items))
        source.last_fetched_at = now

        # Companion sources (same feed, different users) — no extra HTTP request
        for cid in (companion_ids or []):
            companion = db.get(Source, uuid.UUID(cid))
            if not companion or not companion.is_active:
                continue
            all_new_item_ids.extend(_save_items_for_source(db, companion, raw_items))
            companion.last_fetched_at = now

        db.commit()

        if all_new_item_ids:
            cluster_map = cluster_new_items(db, all_new_item_ids)
            db.commit()

            dispatched_clusters: set[uuid.UUID] = set()
            for item_id, cluster_id in cluster_map.items():
                if cluster_id is not None:
                    if cluster_id not in dispatched_clusters:
                        process_cluster.apply_async(args=[str(cluster_id)], queue="process")
                        dispatched_clusters.add(cluster_id)
                else:
                    process_news_item.apply_async(args=[str(item_id)], queue="process")

        return {"source_id": source_id, "new_items": len(all_new_item_ids), "companions": len(companion_ids or [])}

    except Exception as exc:
        db.rollback()
        logger.exception("Error fetching source %s", source_id)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
    finally:
        db.close()


@celery_app.task(name="app.tasks.fetch_tasks.fetch_all_sources", queue="fetch")
def fetch_all_sources() -> None:
    """Schedule fetches, deduplicating across users with identical source configs.
    Sources with the same (source_type, config) are fetched once; results are
    fanned out to all users who have that source configured."""
    db = SessionLocal()
    try:
        now = datetime.now(tz=timezone.utc)
        all_sources = db.scalars(select(Source).where(Source.is_active == True)).all()  # noqa: E712

        # Group all active sources by their fetch identity
        groups: dict[str, list[Source]] = defaultdict(list)
        for source in all_sources:
            groups[_config_key(source)].append(source)

        dispatched = 0
        for key, group in groups.items():
            # A group needs fetching if any member is due
            due = [
                s for s in group
                if s.last_fetched_at is None or (now - s.last_fetched_at) >= timedelta(seconds=s.fetch_interval)
            ]
            if not due:
                continue

            # Use the shortest remaining interval as the primary (most eager fetcher leads)
            primary = min(due, key=lambda s: s.fetch_interval)
            companions = [s for s in group if s.id != primary.id]

            fetch_source.apply_async(
                args=[str(primary.id)],
                kwargs={"companion_ids": [str(s.id) for s in companions]},
                queue="fetch",
            )
            dispatched += 1
            logger.debug("Dispatched fetch for '%s' with %d companion(s)", primary.name, len(companions))

        logger.info("fetch_all_sources: dispatched %d task(s) for %d source group(s)", dispatched, len(groups))
    finally:
        db.close()


@celery_app.task(name="app.tasks.fetch_tasks.cleanup_old_items", queue="default")
def cleanup_old_items(days: int = 30) -> int:
    from sqlalchemy import delete as sa_delete
    db = SessionLocal()
    try:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
        count = db.scalar(
            select(func.count()).select_from(NewsItem).where(
                NewsItem.fetched_at < cutoff,
                NewsItem.is_relevant == False,  # noqa: E712
                NewsItem.read_later == False,  # noqa: E712
            )
        ) or 0
        db.execute(
            sa_delete(NewsItem).where(
                NewsItem.fetched_at < cutoff,
                NewsItem.is_relevant == False,  # noqa: E712
                NewsItem.read_later == False,  # noqa: E712
            )
        )
        # Remove clusters that lost all their items
        db.execute(
            sa_delete(NewsCluster).where(
                ~exists(select(NewsItem.id).where(NewsItem.cluster_id == NewsCluster.id))
            )
        )
        db.commit()
        logger.info("Cleaned up %d old news items", count)
        return count
    finally:
        db.close()
