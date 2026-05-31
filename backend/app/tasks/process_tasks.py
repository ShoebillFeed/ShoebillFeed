import logging
import uuid

import anthropic as anthropic_sdk
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import NewsItem, Category, NewsCluster, Source
from app.models.user_settings import UserSettings
from app.services.deduplication import url_hash
from app.services.llm.factory import get_llm_provider
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_output_language(db, user_id) -> str | None:
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
    return s.output_language if s else None


def _get_categories_payload(db, user_id) -> list[dict]:
    categories = db.scalars(select(Category).where(Category.user_id == user_id, Category.is_active == True)).all()  # noqa: E712
    payload = []
    for c in categories:
        entry: dict = {"name": c.name, "keywords": c.keywords}
        if c.prompt:
            entry["description"] = c.prompt
        payload.append(entry)
    return payload


def _expand_newsletter(db, email_item: "NewsItem", source: "Source", categories_payload, provider, output_language=None) -> None:
    """Replace a newsletter email item with individual extracted news items."""
    try:
        result = provider.extract_newsletter_items(
            content=email_item.raw_content or email_item.title,
            categories=categories_payload,
            output_language=output_language,
        )
    except Exception:
        logger.exception("Newsletter extraction failed for item %s, falling back to normal processing", email_item.id)
        # Fall back: treat it like a regular article
        email_item.llm_processed = True
        return

    logger.info("Newsletter extraction for %s: LLM returned %d items", email_item.id, len(result.items))

    if not result.items:
        logger.warning("Newsletter extraction returned 0 items for %s, falling back", email_item.id)
        email_item.llm_processed = True
        return

    cat_objects = {
        cat.name: cat
        for cat in db.scalars(
            select(Category).where(Category.user_id == email_item.user_id, Category.is_active == True)  # noqa: E712
        ).all()
    }

    new_item_ids = []
    skipped_dupes = 0
    for ni in result.items:
        logger.debug("Newsletter item: headline=%r url=%r", ni.headline, ni.url)
        # Use email URL as fallback so the item is still identifiable
        item_url = ni.url or email_item.url
        h = url_hash(item_url)
        if db.scalar(select(NewsItem.id).where(NewsItem.url_hash == h)):
            skipped_dupes += 1
            continue  # already exists

        new_item = NewsItem(
            source_id=source.id,
            user_id=email_item.user_id,
            title=ni.headline,
            url=item_url,
            url_hash=h,
            raw_content=None,
            published_at=email_item.published_at,
            abstract=ni.summary,
            extracted_keywords=ni.keywords or None,
            relevance_score=ni.relevance_score,
            impact_score=ni.impact_score,
            llm_processed=True,
        )
        if ni.category_names:
            new_item.categories = [cat_objects[n] for n in ni.category_names if n in cat_objects]
        db.add(new_item)
        db.flush()
        new_item_ids.append(new_item.id)

    logger.info("Newsletter %s: created %d new items, skipped %d duplicates", email_item.id, len(new_item_ids), skipped_dupes)

    # Remove the original email wrapper item
    db.delete(email_item)

    # Trigger clustering for the freshly created items
    if new_item_ids:
        from app.services.clustering import cluster_new_items
        cluster_map = cluster_new_items(db, new_item_ids)
        db.flush()
        # Dispatch process_cluster for any new clusters
        from app.tasks.process_tasks import process_cluster
        dispatched: set = set()
        for item_id, cluster_id in cluster_map.items():
            if cluster_id and cluster_id not in dispatched:
                process_cluster.apply_async(args=[str(cluster_id)], queue="process")
                dispatched.add(cluster_id)


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
        output_language = _get_output_language(db, item.user_id)
        provider = get_llm_provider()

        source = db.get(Source, item.source_id) if item.source_id else None

        # Newsletter emails: extract individual articles via LLM, then replace this item
        if source is not None and source.source_type == "email":
            _expand_newsletter(db, item, source, categories_payload, provider, output_language)
            db.commit()
            logger.info("Expanded newsletter email %s into individual items", news_item_id)
            return

        is_social = source is not None and source.source_type == "mastodon"

        result = provider.process_item(
            title=item.title,
            content=item.raw_content or "",
            categories=categories_payload,
            social_post=is_social,
            output_language=output_language,
        )

        if is_social and result.generated_title:
            item.title = result.generated_title
            item.abstract = item.raw_content or ""
        else:
            item.abstract = result.abstract
        item.extracted_keywords = result.keywords or None
        item.relevance_score = result.relevance_score
        item.impact_score = result.impact_score
        item.llm_processed = True

        if result.category_names:
            cats = db.scalars(
                select(Category).where(
                    Category.name.in_(result.category_names),
                    Category.user_id == item.user_id,
                )
            ).all()
            item.categories = list(cats)

        db.commit()
        logger.info("Processed news item %s", news_item_id)

    except anthropic_sdk.RateLimitError as exc:
        db.rollback()
        retry_after = int(exc.response.headers.get("retry-after", 60))
        countdown = max(retry_after, 30) + self.request.retries * 15
        logger.warning("Rate limited processing item %s, retrying in %ds", news_item_id, countdown)
        raise self.retry(exc=exc, max_retries=10, countdown=countdown)
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
        output_language = _get_output_language(db, cluster.user_id)
        provider = get_llm_provider()

        items_payload = [
            {
                "title": item.title,
                "content": item.raw_content or "",
                "source_name": item.source.name if item.source else "Unknown",
            }
            for item in items
        ]

        result = provider.process_cluster(items=items_payload, categories=categories_payload, output_language=output_language)

        cluster.title = result.title
        cluster.unified_abstract = result.unified_abstract
        cluster.extracted_keywords = result.keywords or None
        cluster.relevance_score = result.relevance_score
        cluster.impact_score = result.impact_score
        cluster.llm_processed = True

        if result.category_names:
            cats = db.scalars(
                select(Category).where(
                    Category.name.in_(result.category_names),
                    Category.user_id == cluster.user_id,
                )
            ).all()
            cluster.categories = list(cats)

        for i, item in enumerate(items):
            item.source_summary = result.source_summaries.get(f"item_{i}", "")
            item.llm_processed = True

        db.commit()
        logger.info("Processed cluster %s (%d items)", cluster_id, len(items))

    except anthropic_sdk.RateLimitError as exc:
        db.rollback()
        retry_after = int(exc.response.headers.get("retry-after", 60))
        countdown = max(retry_after, 30) + self.request.retries * 15
        logger.warning("Rate limited processing cluster %s, retrying in %ds", cluster_id, countdown)
        raise self.retry(exc=exc, max_retries=10, countdown=countdown)
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
        for i, item_id in enumerate(item_ids):
            process_news_item.apply_async(args=[str(item_id)], queue="process", countdown=i * 2)

        # Unprocessed clusters
        cluster_ids = db.scalars(
            select(NewsCluster.id).where(NewsCluster.llm_processed == False).limit(limit)  # noqa: E712
        ).all()
        offset = len(item_ids)
        for i, cid in enumerate(cluster_ids):
            process_cluster.apply_async(args=[str(cid)], queue="process", countdown=(offset + i) * 2)

        return len(item_ids) + len(cluster_ids)
    finally:
        db.close()
