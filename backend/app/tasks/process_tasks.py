import logging
import uuid
from datetime import datetime, timedelta, timezone

import anthropic as anthropic_sdk
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.config import get_settings
from app.database import SessionLocal
from app.models import NewsItem, Category, NewsCluster, Source
from app.models.llm_batch import LLMBatch
from app.models.user_settings import UserSettings
from app.services.clustering import recluster_processed_item
from app.services.deduplication import url_hash
from app.services.llm.base import dedup_cluster_payload
from app.services.llm.factory import get_llm_provider, get_anthropic_provider
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
        if db.scalar(select(NewsItem.id).where(
            NewsItem.url_hash == h,
            NewsItem.user_id == email_item.user_id,
        )):
            skipped_dupes += 1
            continue  # already exists for this user

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

        user_settings = db.scalar(select(UserSettings).where(UserSettings.user_id == item.user_id))
        output_language = user_settings.output_language if user_settings else None
        min_word_count = user_settings.llm_min_word_count if user_settings else 50
        categories_payload = _get_categories_payload(db, item.user_id)
        provider = get_llm_provider()

        source = db.get(Source, item.source_id) if item.source_id else None

        # Newsletter emails: extract individual articles via LLM, then replace this item
        if source is not None and source.source_type == "email":
            _expand_newsletter(db, item, source, categories_payload, provider, output_language)
            db.commit()
            logger.info("Expanded newsletter email %s into individual items", news_item_id)
            return

        is_social = source is not None and source.source_type == "mastodon"

        word_count = len((item.title + " " + (item.raw_content or "")).split())
        is_short = word_count <= min_word_count
        translating = output_language is not None

        if is_short and not translating:
            # E: items below llm_min_word_count get classify-only, no abstract generation
            result = provider.process_short_item(
                title=item.title,
                content=item.raw_content or "",
                categories=categories_payload,
            )
            item.abstract = item.raw_content or item.title
        elif is_social:
            result = provider.process_item(
                title=item.title,
                content=item.raw_content or "",
                categories=categories_payload,
                social_post=True,
                output_language=output_language,
            )
            if result.generated_title:
                item.title = result.generated_title
                item.abstract = item.raw_content or ""
            else:
                item.abstract = result.abstract
        elif translating:
            # Translation mode: always run full processing so abstract + title get translated,
            # skipping the cost shortcuts below that would otherwise leave items untranslated.
            result = provider.process_item(
                title=item.title,
                content=item.raw_content or "",
                categories=categories_payload,
                output_language=output_language,
            )
            item.abstract = result.abstract
            if result.generated_title:
                item.title = result.generated_title
        else:
            # A: two-stage pipeline for regular articles
            # Stage 1 — cheap classify-only with 200-char excerpt; no abstract requested
            stage1 = provider.process_short_item(
                title=item.title,
                content=(item.raw_content or "")[:200],
                categories=categories_payload,
            )
            if stage1.category_names or not categories_payload:
                # Category matched (or user has no categories) → Stage 2: full abstract
                result = provider.process_item(
                    title=item.title,
                    content=item.raw_content or "",
                    categories=categories_payload,
                    output_language=output_language,
                )
                item.abstract = result.abstract
            else:
                # No category matched → skip Stage 2, use raw content as abstract
                result = stage1
                item.abstract = item.raw_content or item.title
        item.extracted_keywords = result.keywords or None
        item.relevance_score = result.relevance_score
        item.impact_score = result.impact_score
        item.llm_processed = True
        item.llm_provider = result.provider_name or None
        item.llm_model = result.model_name or None

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

        try:
            from app.services.push_service import notify_item
            notify_item(db, item)
        except Exception:
            logger.exception("Push notification failed for item %s", news_item_id)

        # Second-pass keyword clustering for standalone items
        if item.cluster_id is None:
            cluster_id = recluster_processed_item(db, item)
            if cluster_id:
                db.commit()
                logger.info("Keyword-clustered item %s into cluster %s", news_item_id, cluster_id)
                process_cluster.apply_async(args=[str(cluster_id)], queue="process")

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

        all_items_payload = [
            {
                "title": item.title,
                "content": item.raw_content or "",
                "source_name": item.source.name if item.source else "Unknown",
            }
            for item in items
        ]

        # Deduplicate identical content before sending to LLM to save tokens
        dedup_items, orig_to_dedup = dedup_cluster_payload(all_items_payload)

        result = provider.process_cluster(items=dedup_items, categories=categories_payload, output_language=output_language)

        cluster.title = result.title
        cluster.unified_abstract = result.unified_abstract
        cluster.extracted_keywords = result.keywords or None
        cluster.relevance_score = result.relevance_score
        cluster.impact_score = result.impact_score
        cluster.llm_processed = True
        cluster.llm_provider = result.provider_name or None
        cluster.llm_model = result.model_name or None

        if result.category_names:
            cats = db.scalars(
                select(Category).where(
                    Category.name.in_(result.category_names),
                    Category.user_id == cluster.user_id,
                )
            ).all()
            cluster.categories = list(cats)

        for i, item in enumerate(items):
            dedup_idx = orig_to_dedup[i]
            item.source_summary = result.source_summaries.get(f"item_{dedup_idx}", "") if dedup_idx is not None else ""
            item.llm_processed = True

        db.commit()
        logger.info("Processed cluster %s (%d items)", cluster_id, len(items))

        try:
            from app.services.push_service import notify_cluster
            notify_cluster(db, cluster, list(items))
        except Exception:
            logger.exception("Push notification failed for cluster %s", cluster_id)

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
    settings = get_settings()
    db = SessionLocal()
    try:
        item_ids = list(db.scalars(
            select(NewsItem.id)
            .where(NewsItem.llm_processed == False, NewsItem.cluster_id == None)  # noqa: E711,E712
            .limit(limit)
        ).all())
        cluster_ids = list(db.scalars(
            select(NewsCluster.id).where(NewsCluster.llm_processed == False).limit(limit)  # noqa: E712
        ).all())

        anthropic = get_anthropic_provider()
        if anthropic is None:
            for i, item_id in enumerate(item_ids):
                process_news_item.apply_async(args=[str(item_id)], queue="process", countdown=i * 2)
            for i, cid in enumerate(cluster_ids):
                process_cluster.apply_async(args=[str(cid)], queue="process", countdown=(len(item_ids) + i) * 2)
            return len(item_ids) + len(cluster_ids)

        # Anthropic batch path — newsletter (email) items must still be processed individually
        email_ids = set(db.scalars(
            select(NewsItem.id)
            .join(Source, NewsItem.source_id == Source.id)
            .where(NewsItem.id.in_(item_ids), Source.source_type == "email")
        ).all())
        for i, item_id in enumerate(email_ids):
            process_news_item.apply_async(args=[str(item_id)], queue="process", countdown=i * 2)

        batch_item_ids = [iid for iid in item_ids if iid not in email_ids]

        from app.services.llm.batch_service import submit_batch
        submit_batch(db, anthropic, batch_item_ids, cluster_ids)
        return len(item_ids) + len(cluster_ids)
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_tasks.poll_llm_batches", queue="process")
def poll_llm_batches() -> None:
    anthropic = get_anthropic_provider()
    if anthropic is None:
        return

    settings = get_settings()
    db = SessionLocal()
    max_wait = timedelta(minutes=settings.llm_batch_max_wait_minutes)
    now = datetime.now(timezone.utc)

    try:
        pending = db.scalars(
            select(LLMBatch).where(LLMBatch.status.in_(["pending", "cancelling"]))
        ).all()

        from app.services.llm.batch_service import apply_batch_results

        for llm_batch in pending:
            try:
                batch_info = anthropic.client.messages.batches.retrieve(llm_batch.anthropic_batch_id)

                if batch_info.processing_status == "ended":
                    results = list(anthropic.client.messages.batches.results(llm_batch.anthropic_batch_id))
                    applied = apply_batch_results(db, llm_batch, results, anthropic)

                    if llm_batch.status == "cancelling":
                        _dispatch_fallback(llm_batch, applied)
                        llm_batch.status = "cancelled"
                        logger.warning(
                            "Batch %s cancelled: %d applied, %d fell back",
                            llm_batch.anthropic_batch_id, len(applied),
                            len(llm_batch.requests) - len(applied),
                        )
                    else:
                        llm_batch.status = "completed"
                        logger.info("Batch %s completed: %d applied", llm_batch.anthropic_batch_id, len(applied))

                    db.commit()

                elif llm_batch.status == "pending":
                    submitted = llm_batch.submitted_at
                    if submitted.tzinfo is None:
                        submitted = submitted.replace(tzinfo=timezone.utc)
                    if now - submitted > max_wait:
                        anthropic.client.messages.batches.cancel(llm_batch.anthropic_batch_id)
                        llm_batch.status = "cancelling"
                        db.commit()
                        logger.warning("Batch %s timed out after %d min, cancelling", llm_batch.anthropic_batch_id, settings.llm_batch_max_wait_minutes)

            except Exception:
                logger.exception("Error polling batch %s", llm_batch.anthropic_batch_id)
    finally:
        db.close()


def _dispatch_fallback(llm_batch: LLMBatch, applied: set[str]) -> None:
    """Dispatch sync tasks for any requests that weren't processed in the batch."""
    for meta in llm_batch.requests:
        if meta["custom_id"] not in applied:
            if meta["item_type"] == "news_item":
                process_news_item.apply_async(args=[meta["item_id"]], queue="process")
            elif meta["item_type"] == "news_item_group":
                for item_id in meta["item_ids"]:
                    process_news_item.apply_async(args=[item_id], queue="process")
            elif meta["item_type"] == "cluster":
                process_cluster.apply_async(args=[meta["item_id"]], queue="process")
