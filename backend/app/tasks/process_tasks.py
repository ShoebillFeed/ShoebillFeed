import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import NewsItem, Category, NewsCluster
from app.services.llm.factory import get_llm_provider
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_categories_payload(db, user_id) -> list[dict]:
    categories = db.scalars(select(Category).where(Category.user_id == user_id)).all()
    payload = []
    for c in categories:
        entry: dict = {"name": c.name, "keywords": c.keywords}
        if c.prompt:
            entry["description"] = c.prompt
        payload.append(entry)
    return payload


@celery_app.task(
    name="app.tasks.process_tasks.process_news_item",
    queue="process",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_news_item(self, news_item_id: str) -> None:
    db = SessionLocal()
    try:
        item = db.get(NewsItem, uuid.UUID(news_item_id))
        if not item or item.llm_processed:
            return

        categories_payload = _get_categories_payload(db, item.user_id)
        provider = get_llm_provider()

        result = provider.process_item(
            title=item.title,
            content=item.raw_content or "",
            categories=categories_payload,
        )

        item.abstract = result.abstract
        item.extracted_keywords = result.keywords or None
        item.relevance_score = result.relevance_score
        item.impact_score = result.impact_score
        item.llm_processed = True

        if result.category_names:
            cats = db.scalars(select(Category).where(Category.name.in_(result.category_names))).all()
            item.categories = list(cats)

        db.commit()
        logger.info("Processed news item %s", news_item_id)

    except Exception as exc:
        db.rollback()
        logger.exception("Error processing news item %s", news_item_id)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.process_tasks.process_cluster",
    queue="process",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_cluster(self, cluster_id: str) -> None:
    db = SessionLocal()
    try:
        cluster = db.get(NewsCluster, uuid.UUID(cluster_id))
        if not cluster or cluster.llm_processed:
            return

        items = db.scalars(
            select(NewsItem)
            .where(NewsItem.cluster_id == cluster.id)
            .options(joinedload(NewsItem.source))
        ).all()

        if len(items) < 2:
            # Disband the cluster and process the lone item as standalone
            if items:
                items[0].cluster_id = None
            db.delete(cluster)
            db.commit()
            if items:
                process_news_item.apply_async(args=[str(items[0].id)], queue="process")
            return

        categories_payload = _get_categories_payload(db, cluster.user_id)
        provider = get_llm_provider()

        items_payload = [
            {
                "title": item.title,
                "content": item.raw_content or "",
                "source_name": item.source.name if item.source else "Unknown",
            }
            for item in items
        ]

        result = provider.process_cluster(items=items_payload, categories=categories_payload)

        cluster.unified_abstract = result.unified_abstract
        cluster.extracted_keywords = result.keywords or None
        cluster.relevance_score = result.relevance_score
        cluster.impact_score = result.impact_score
        cluster.llm_processed = True

        if result.category_names:
            cats = db.scalars(select(Category).where(Category.name.in_(result.category_names))).all()
            cluster.categories = list(cats)

        for i, item in enumerate(items):
            item.source_summary = result.source_summaries.get(f"item_{i}", "")
            item.llm_processed = True

        db.commit()
        logger.info("Processed cluster %s (%d items)", cluster_id, len(items))

    except Exception as exc:
        db.rollback()
        logger.exception("Error processing cluster %s", cluster_id)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_tasks.batch_process_unprocessed", queue="process")
def batch_process_unprocessed(limit: int = 50) -> int:
    db = SessionLocal()
    try:
        # Standalone unprocessed items (not in a cluster)
        item_ids = db.scalars(
            select(NewsItem.id)
            .where(NewsItem.llm_processed == False, NewsItem.cluster_id == None)  # noqa: E711,E712
            .limit(limit)
        ).all()
        for item_id in item_ids:
            process_news_item.apply_async(args=[str(item_id)], queue="process")

        # Unprocessed clusters
        cluster_ids = db.scalars(
            select(NewsCluster.id).where(NewsCluster.llm_processed == False).limit(limit)  # noqa: E712
        ).all()
        for cid in cluster_ids:
            process_cluster.apply_async(args=[str(cid)], queue="process")

        return len(item_ids) + len(cluster_ids)
    finally:
        db.close()
