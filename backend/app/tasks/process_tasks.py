import logging
import uuid
from datetime import datetime, timedelta, timezone

import anthropic as anthropic_sdk
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.config import get_settings
from app.database import SessionLocal
from app.models import NewsItem, Category, NewsCluster, Source
from app.models.category_weight import CategoryWeight
from app.models.user import User
from app.models.llm_batch import LLMBatch
from app.models.user_settings import UserSettings
from app.services.clustering import recluster_processed_item
from app.services.scoring import decay_learned_weights
from app.services.deduplication import url_hash
from app.services.embedding import generate_embedding
from app.services.llm.base import dedup_cluster_payload
from app.services.llm.factory import get_llm_provider, get_anthropic_provider
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_output_language(db, user_id) -> str | None:
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
    return s.output_language if s else None


_MAX_LLM_CATEGORIES = 25


def _get_categories_payload(db, user_id) -> list[dict]:
    categories = list(db.scalars(
        select(Category).where(Category.user_id == user_id, Category.is_active == True)  # noqa: E712
    ).all())
    if len(categories) > _MAX_LLM_CATEGORIES:
        weights = {
            cw.category_id: cw.weight
            for cw in db.scalars(select(CategoryWeight).where(CategoryWeight.user_id == user_id)).all()
        }
        categories = sorted(categories, key=lambda c: weights.get(c.id, 1.0), reverse=True)[:_MAX_LLM_CATEGORIES]
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
        email_item.llm_provider = provider.provider_name or None
        email_item.llm_model = provider.model_name or None
        return

    logger.info("Newsletter extraction for %s: LLM returned %d items", email_item.id, len(result.items))

    if not result.items:
        logger.warning("Newsletter extraction returned 0 items for %s, falling back", email_item.id)
        email_item.llm_processed = True
        email_item.llm_provider = provider.provider_name or None
        email_item.llm_model = provider.model_name or None
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
            llm_provider=result.provider_name or None,
            llm_model=result.model_name or None,
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
    soft_time_limit=1200,
    time_limit=1500,
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
            # Stage 1 — cheap classify-only with a longer excerpt; no abstract requested.
            # 200 chars was too short and risked missing the article's actual topic,
            # causing false negatives that skipped Stage 2 entirely.
            stage1 = provider.process_short_item(
                title=item.title,
                content=(item.raw_content or "")[:600],
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

        embedding = generate_embedding(f"{item.title}\n{item.abstract or ''}")
        if embedding is not None:
            item.embedding = embedding

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

        from app.services.llm.batch_service import propagate_llm_results
        propagated = propagate_llm_results(db, item)
        if propagated:
            db.commit()
            logger.debug("Propagated LLM results to %d same-URL item(s) for other users", propagated)

        try:
            from app.services.push_service import notify_item
            notify_item(db, item)
        except Exception:
            logger.exception("Push notification failed for item %s", news_item_id)

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
        # Second-pass keyword clustering runs outside the main try/except so a
        # recluster failure does not retry the whole task (item is already processed).
        if not db.is_active:
            db.close()
            return
        try:
            item = db.get(NewsItem, uuid.UUID(news_item_id))
            if item and item.llm_processed and item.cluster_id is None:
                cluster_id = recluster_processed_item(db, item)
                if cluster_id:
                    db.commit()
                    logger.info("Keyword-clustered item %s into cluster %s", news_item_id, cluster_id)
                    process_cluster.apply_async(args=[str(cluster_id)], queue="process")
        except Exception:
            logger.exception("Reclustering failed for item %s — skipping", news_item_id)
            db.rollback()
        finally:
            db.close()


@celery_app.task(
    name="app.tasks.process_tasks.process_cluster",
    queue="process",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1200,
    time_limit=1500,
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
def batch_process_unprocessed(limit: int = 150) -> int:
    settings = get_settings()
    db = SessionLocal()
    try:
        # Distribute limit fairly across users to prevent one user starving others
        user_ids = list(db.scalars(select(User.id)).all())
        if not user_ids:
            return 0
        per_user = max(1, limit // len(user_ids))

        item_ids = []
        for uid in user_ids:
            item_ids.extend(db.scalars(
                select(NewsItem.id)
                .where(NewsItem.llm_processed == False, NewsItem.cluster_id == None, NewsItem.user_id == uid)  # noqa: E711,E712
                .limit(per_user)
            ).all())

        cluster_ids = []
        for uid in user_ids:
            cluster_ids.extend(db.scalars(
                select(NewsCluster.id)
                .where(NewsCluster.llm_processed == False, NewsCluster.user_id == uid)  # noqa: E712
                .limit(per_user)
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


@celery_app.task(name="app.tasks.process_tasks._poll_single_batch", queue="process", bind=True, max_retries=2)
def _poll_single_batch(self, llm_batch_id: str) -> None:
    """Poll and apply results for one LLM batch. Runs as a separate task so N batches run concurrently."""
    anthropic = get_anthropic_provider()
    if anthropic is None:
        return

    settings = get_settings()
    db = SessionLocal()
    max_wait = timedelta(minutes=settings.llm_batch_max_wait_minutes)
    now = datetime.now(timezone.utc)

    try:
        llm_batch = db.get(LLMBatch, uuid.UUID(llm_batch_id))
        if not llm_batch or llm_batch.status not in ("pending", "cancelling"):
            return

        from app.services.llm.batch_service import apply_batch_results

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
                logger.warning("Batch %s timed out after %d min, cancelling",
                               llm_batch.anthropic_batch_id, settings.llm_batch_max_wait_minutes)

    except Exception as exc:
        db.rollback()
        logger.exception("Error polling batch %s", llm_batch_id)
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_tasks.poll_llm_batches", queue="process")
def poll_llm_batches() -> None:
    """Dispatch one _poll_single_batch task per pending batch so polls run concurrently."""
    anthropic = get_anthropic_provider()
    if anthropic is None:
        return

    db = SessionLocal()
    try:
        pending_ids = list(db.scalars(
            select(LLMBatch.id).where(LLMBatch.status.in_(["pending", "cancelling"]))
        ).all())
    finally:
        db.close()

    for batch_id in pending_ids:
        _poll_single_batch.apply_async(args=[str(batch_id)], queue="process")

    if pending_ids:
        logger.info("poll_llm_batches: dispatched %d polling task(s)", len(pending_ids))


@celery_app.task(name="app.tasks.process_tasks._recalculate_weights", queue="default")
def _recalculate_weights(
    user_id: str,
    category_ids: list[str],
    liked_item_id: str | None = None,
    disliked_item_id: str | None = None,
) -> None:
    """Recompute category/keyword weights in the background after a user action.

    Called from API handlers so they can return immediately without doing N DB
    round-trips per liked/disliked/shown category. Runs on the default queue
    (separate from LLM processing) so heavy scoring work never blocks fetches.
    """
    from app.services.scoring import (
        update_category_weight, update_keyword_weights,
        apply_keyword_penalty, update_category_keyword_weights,
    )
    db = SessionLocal()
    try:
        uid = uuid.UUID(user_id)
        user_settings = db.scalar(select(UserSettings).where(UserSettings.user_id == uid))
        base = user_settings.weight_base if user_settings else 1.0
        multiplier = user_settings.weight_log_multiplier if user_settings else 0.5
        window_days = user_settings.learning_window_days if user_settings else 90
        ignore_penalty = user_settings.ignore_penalty_weight if user_settings else 0.1

        for cat_id_str in category_ids:
            try:
                update_category_weight(
                    db, uuid.UUID(cat_id_str),
                    base=base, multiplier=multiplier,
                    window_days=window_days, ignore_penalty=ignore_penalty,
                )
            except Exception:
                logger.exception("update_category_weight failed for %s", cat_id_str)
                db.rollback()

        if liked_item_id:
            item = db.get(NewsItem, uuid.UUID(liked_item_id))
            if item and item.extracted_keywords:
                update_keyword_weights(db, item.extracted_keywords, uid)
                for cat in item.categories:
                    update_category_keyword_weights(db, item.extracted_keywords, cat.id, uid)
                db.commit()

        if disliked_item_id:
            item = db.get(NewsItem, uuid.UUID(disliked_item_id))
            if item and item.extracted_keywords:
                apply_keyword_penalty(db, item.extracted_keywords, uid)

    except Exception:
        logger.exception("Weight recalculation failed for user %s", user_id)
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_tasks.refresh_keyword_clusters", queue="default")
def refresh_keyword_clusters() -> None:
    from app.services.keyword_clustering import refresh_clusters_for_user
    db = SessionLocal()
    try:
        user_ids = list(db.scalars(select(User.id)).all())
        for user_id in user_ids:
            try:
                refresh_clusters_for_user(db, user_id)
            except Exception:
                logger.exception("Keyword cluster refresh failed for user %s", user_id)
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


@celery_app.task(name="app.tasks.process_tasks.decay_weights", bind=True, max_retries=2)
def decay_weights(self) -> dict:
    """Daily slow decay of all learned keyword and category weights, per user settings."""
    import math
    from app.models.user_settings import UserSettings

    # weight of a single like — threshold at which a row is considered neutral and pruned
    BASELINE_WEIGHT = 1.0 + math.log1p(1) * 0.5
    PRUNE_THRESHOLD = 1.001

    db = SessionLocal()
    try:
        user_factors: dict = {}
        for us in db.scalars(select(UserSettings)).all():
            days = us.weight_decay_days
            if days and days > 0:
                user_factors[us.user_id] = (PRUNE_THRESHOLD / BASELINE_WEIGHT) ** (1.0 / days)

        if not user_factors:
            return {"skipped": "no users with decay enabled"}

        result = decay_learned_weights(db, user_factors)
        logger.info("Weight decay complete: %s", result)
        return result
    except Exception as exc:
        db.rollback()
        logger.exception("Weight decay failed")
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()
