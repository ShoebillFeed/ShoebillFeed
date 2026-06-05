import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import NewsItem, NewsCluster, Source, Category
from app.models.llm_batch import LLMBatch
from app.models.user_settings import UserSettings
from app.services.llm.base import parse_llm_response, parse_short_llm_response, parse_cluster_response

logger = logging.getLogger(__name__)


def _categories_payload(db: Session, user_id) -> list[dict]:
    categories = db.scalars(
        select(Category).where(Category.user_id == user_id, Category.is_active == True)  # noqa: E712
    ).all()
    result = []
    for c in categories:
        entry = {"name": c.name, "keywords": c.keywords}
        if c.prompt:
            entry["description"] = c.prompt
        result.append(entry)
    return result


def _output_language(db: Session, user_id) -> str | None:
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
    return s.output_language if s else None


def _min_word_count(db: Session, user_id) -> int:
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
    return s.llm_min_word_count if s else 50


def submit_batch(db: Session, provider, item_ids: list, cluster_ids: list) -> "LLMBatch | None":
    """Build and submit an Anthropic message batch. Returns the saved LLMBatch or None if empty."""
    user_cats: dict = {}
    user_langs: dict = {}
    user_min_words: dict = {}

    def _load_user(user_id):
        uid = str(user_id)
        if uid not in user_cats:
            user_cats[uid] = _categories_payload(db, user_id)
            user_langs[uid] = _output_language(db, user_id)
            user_min_words[uid] = _min_word_count(db, user_id)

    batch_requests = []
    request_meta = []

    for item_id in item_ids:
        item = db.get(NewsItem, item_id)
        if not item or item.llm_processed:
            continue
        source = db.get(Source, item.source_id) if item.source_id else None
        _load_user(item.user_id)
        uid = str(item.user_id)
        is_social = source is not None and source.source_type == "mastodon"
        word_count = len((item.title + " " + (item.raw_content or "")).split())
        is_short = word_count <= user_min_words[uid]

        custom_id = f"item_{item.id}"
        batch_requests.append(provider.build_item_request(
            custom_id=custom_id,
            title=item.title,
            content=item.raw_content or "",
            categories=user_cats[uid],
            is_short=is_short,
            social_post=is_social,
            output_language=user_langs[uid],
        ))
        request_meta.append({
            "custom_id": custom_id,
            "item_id": str(item.id),
            "item_type": "news_item",
            "is_short": is_short,
            "social_post": is_social,
        })

    for cluster_id in cluster_ids:
        cluster = db.get(NewsCluster, cluster_id)
        if not cluster or cluster.llm_processed:
            continue
        items = db.scalars(
            select(NewsItem)
            .where(NewsItem.cluster_id == cluster.id)
            .options(joinedload(NewsItem.source))
        ).all()
        if len(items) < 2:
            continue
        _load_user(cluster.user_id)
        uid = str(cluster.user_id)
        items_payload = [
            {
                "title": i.title,
                "content": i.raw_content or "",
                "source_name": i.source.name if i.source else "Unknown",
            }
            for i in items
        ]
        custom_id = f"cluster_{cluster.id}"
        batch_requests.append(provider.build_cluster_request(
            custom_id=custom_id,
            items=items_payload,
            categories=user_cats[uid],
            output_language=user_langs[uid],
        ))
        request_meta.append({
            "custom_id": custom_id,
            "item_id": str(cluster.id),
            "item_type": "cluster",
            "item_count": len(items),
        })

    if not batch_requests:
        return None

    batch = provider.client.messages.batches.create(requests=batch_requests)
    llm_batch = LLMBatch(
        anthropic_batch_id=batch.id,
        submitted_at=datetime.now(timezone.utc),
        status="pending",
        requests=request_meta,
    )
    db.add(llm_batch)
    db.commit()
    logger.info("Submitted Anthropic batch %s with %d requests", batch.id, len(batch_requests))
    return llm_batch


def apply_batch_results(db: Session, llm_batch: LLMBatch, results) -> set[str]:
    """Write LLM results to DB. Returns the set of successfully applied custom_ids."""
    meta_by_id = {r["custom_id"]: r for r in llm_batch.requests}
    applied: set[str] = set()

    for result in results:
        cid = result.custom_id
        meta = meta_by_id.get(cid)
        if not meta:
            continue
        if result.result.type != "succeeded":
            logger.warning("Batch request %s: %s", cid, result.result.type)
            continue
        text = result.result.message.content[0].text
        try:
            if meta["item_type"] == "news_item":
                _apply_item_result(db, meta, text)
            else:
                _apply_cluster_result(db, meta, text)
            applied.add(cid)
        except Exception:
            logger.exception("Failed to apply result for %s", cid)

    db.commit()
    return applied


def _apply_item_result(db: Session, meta: dict, text: str) -> None:
    item = db.get(NewsItem, meta["item_id"])
    if not item or item.llm_processed:
        return

    known = [c.name for c in db.scalars(
        select(Category).where(Category.user_id == item.user_id, Category.is_active == True)  # noqa: E712
    ).all()]

    if meta.get("is_short"):
        result = parse_short_llm_response(text, known)
        item.abstract = item.raw_content or item.title
    else:
        result = parse_llm_response(text, known, social_post=meta.get("social_post", False))
        if meta.get("social_post") and result.generated_title:
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


def _apply_cluster_result(db: Session, meta: dict, text: str) -> None:
    cluster = db.get(NewsCluster, meta["item_id"])
    if not cluster or cluster.llm_processed:
        return

    known = [c.name for c in db.scalars(
        select(Category).where(Category.user_id == cluster.user_id, Category.is_active == True)  # noqa: E712
    ).all()]

    result = parse_cluster_response(text, meta.get("item_count", 0), known)
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

    items = db.scalars(select(NewsItem).where(NewsItem.cluster_id == cluster.id)).all()
    for i, item in enumerate(items):
        item.source_summary = result.source_summaries.get(f"item_{i}", "")
        item.llm_processed = True
