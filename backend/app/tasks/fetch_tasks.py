import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, update, exists

from app.database import SessionLocal
from app.models import NewsItem, NewsCluster, Source
from app.services.deduplication import url_hash, content_hash
from app.services.fetchers.base import get_fetcher
from app.services.clustering import cluster_new_items
import app.services.fetchers.rss  # noqa: F401 — register fetchers
import app.services.fetchers.reddit  # noqa: F401
import app.services.fetchers.youtube  # noqa: F401
import app.services.fetchers.email_imap  # noqa: F401
import app.services.fetchers.mastodon  # noqa: F401
import app.services.fetchers.scholar  # noqa: F401
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.fetch_tasks.fetch_source", queue="fetch", bind=True, max_retries=3)
def fetch_source(self, source_id: str) -> dict:
    from app.tasks.process_tasks import process_news_item, process_cluster

    db = SessionLocal()
    try:
        source = db.get(Source, uuid.UUID(source_id))
        if not source or not source.is_active:
            return {"skipped": True}

        fetcher = get_fetcher(source.source_type, source.config)
        raw_items = fetcher.fetch()
        logger.info("Fetched %d raw items from source %s", len(raw_items), source.name)

        new_count = 0
        skipped = 0
        new_item_ids: list[uuid.UUID] = []
        for raw in raw_items:
            h = url_hash(raw.url)
            existing = db.scalar(select(NewsItem.id).where(NewsItem.url_hash == h))
            if existing:
                skipped += 1
                continue

            item = NewsItem(
                source_id=source.id,
                user_id=source.user_id,
                title=raw.title,
                url=raw.url,
                url_hash=h,
                content_hash=content_hash(raw.raw_content) if raw.raw_content else None,
                raw_content=raw.raw_content,
                published_at=raw.published_at,
                image_url=raw.image_url,
            )
            db.add(item)
            db.flush()
            new_item_ids.append(item.id)
            new_count += 1

        source.last_fetched_at = datetime.now(tz=timezone.utc)
        db.commit()
        logger.info("Fetched source %s: %d new, %d duplicate", source.name, new_count, skipped)

        if new_item_ids:
            cluster_map = cluster_new_items(db, new_item_ids)
            db.commit()

            dispatched_clusters: set[uuid.UUID] = set()
            for item_id, cluster_id in cluster_map.items():
                if cluster_id is not None:
                    if cluster_id not in dispatched_clusters:
                        process_cluster.apply_async(args=[str(cluster_id)], queue="process")
                        dispatched_clusters.add(cluster_id)
                else:
                    process_news_item.apply_async(args=[str(item_id)], queue="process")

        return {"source_id": source_id, "new_items": new_count}

    except Exception as exc:
        db.rollback()
        logger.exception("Error fetching source %s", source_id)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
    finally:
        db.close()


@celery_app.task(name="app.tasks.fetch_tasks.fetch_all_sources", queue="fetch")
def fetch_all_sources() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(tz=timezone.utc)
        sources = db.scalars(select(Source).where(Source.is_active == True)).all()  # noqa: E712
        for source in sources:
            interval = timedelta(seconds=source.fetch_interval)
            if source.last_fetched_at is None or (now - source.last_fetched_at) >= interval:
                fetch_source.apply_async(args=[str(source.id)], queue="fetch")
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
