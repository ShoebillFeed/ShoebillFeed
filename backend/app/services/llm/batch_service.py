import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import NewsItem, NewsCluster, Source, Category
from app.models.llm_batch import LLMBatch
from app.models.category_weight import CategoryWeight
from app.models.user_settings import UserSettings
from app.services.llm.base import (
    dedup_cluster_payload,
    parse_cluster_response,
    parse_multi_item_response,
)

logger = logging.getLogger(__name__)

ITEMS_PER_GROUP = 8
MAX_LLM_CATEGORIES = 25


def _categories_payload(db: Session, user_id) -> list[dict]:
    categories = list(db.scalars(
        select(Category).where(Category.user_id == user_id, Category.is_active == True)  # noqa: E712
    ).all())
    if len(categories) > MAX_LLM_CATEGORIES:
        weights = {
            cw.category_id: cw.weight
            for cw in db.scalars(select(CategoryWeight).where(CategoryWeight.user_id == user_id)).all()
        }
        categories = sorted(categories, key=lambda c: weights.get(c.id, 1.0), reverse=True)[:MAX_LLM_CATEGORIES]
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
    return s.llm_min_word_count if s else 100


def propagate_llm_results(db: Session, donor: "NewsItem") -> int:
    """Copy LLM results from a just-processed item to same-URL items for other users that aren't yet processed."""
    if not donor.url_hash:
        return 0
    recipients = db.scalars(
        select(NewsItem).where(
            NewsItem.url_hash == donor.url_hash,
            NewsItem.user_id != donor.user_id,
            NewsItem.llm_processed == False,  # noqa: E712
        )
    ).all()
    if not recipients:
        return 0
    for item in recipients:
        item.abstract = donor.abstract
        item.extracted_keywords = donor.extracted_keywords
        item.impact_score = donor.impact_score
        item.relevance_score = donor.relevance_score
        item.llm_processed = True
        item.llm_provider = donor.llm_provider
        item.llm_model = donor.llm_model
        if donor.extracted_keywords and item.user_id:
            kw_lower = {k.lower() for k in donor.extracted_keywords}
            user_cats = db.scalars(
                select(Category).where(Category.user_id == item.user_id, Category.is_active == True)  # noqa: E712
            ).all()
            item.categories = [cat for cat in user_cats if any(k.lower() in kw_lower for k in cat.keywords)]
    return len(recipients)


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

    # Bulk-load all items with their sources in a single query
    items_by_id: dict = {}
    if item_ids:
        items_by_id = {
            item.id: item
            for item in db.scalars(
                select(NewsItem).where(NewsItem.id.in_(item_ids)).options(joinedload(NewsItem.source))
            ).all()
        }

    # Collect items into groups keyed by (user_id, group_type)
    groups: dict[tuple, list[dict]] = {}

    for item_id in item_ids:
        item = items_by_id.get(item_id)
        if not item or item.llm_processed:
            continue
        _load_user(item.user_id)
        uid = str(item.user_id)
        is_social = item.source is not None and item.source.source_type == "mastodon"
        word_count = len((item.title + " " + (item.raw_content or "")).split())
        is_short = word_count <= user_min_words[uid] and not user_langs[uid]
        group_type = "social" if is_social else ("short" if is_short else "full")

        groups.setdefault((uid, group_type), []).append({
            "id": str(item.id),
            "title": item.title,
            "content": item.raw_content or "",
        })

    batch_requests = []
    request_meta = []

    # One multi-item request per chunk of ITEMS_PER_GROUP
    for (uid, group_type), items_list in groups.items():
        for i in range(0, len(items_list), ITEMS_PER_GROUP):
            chunk = items_list[i:i + ITEMS_PER_GROUP]
            custom_id = f"grp_{uuid.uuid4().hex[:16]}"
            batch_requests.append(provider.build_multi_item_request(
                custom_id=custom_id,
                items=chunk,
                categories=user_cats[uid],
                group_type=group_type,
                output_language=user_langs[uid],
            ))
            request_meta.append({
                "custom_id": custom_id,
                "item_ids": [it["id"] for it in chunk],
                "item_type": "news_item_group",
                "group_type": group_type,
            })

    # Bulk-load clusters and all their items in two queries
    clusters_by_id: dict = {}
    cluster_items: dict = defaultdict(list)
    if cluster_ids:
        clusters_by_id = {
            c.id: c
            for c in db.scalars(select(NewsCluster).where(NewsCluster.id.in_(cluster_ids))).all()
        }
        active_cluster_ids = [cid for cid, c in clusters_by_id.items() if not c.llm_processed]
        if active_cluster_ids:
            for ci in db.scalars(
                select(NewsItem)
                .where(NewsItem.cluster_id.in_(active_cluster_ids))
                .options(joinedload(NewsItem.source))
            ).all():
                cluster_items[ci.cluster_id].append(ci)

    # Clusters remain as individual requests (already multi-item by nature)
    for cluster_id in cluster_ids:
        cluster = clusters_by_id.get(cluster_id)
        if not cluster or cluster.llm_processed:
            continue
        items = cluster_items[cluster.id]
        if len(items) < 2:
            continue
        _load_user(cluster.user_id)
        uid = str(cluster.user_id)
        all_items_payload = [
            {
                "title": i.title,
                "content": i.raw_content or "",
                "source_name": i.source.name if i.source else "Unknown",
            }
            for i in items
        ]
        dedup_items, orig_to_dedup = dedup_cluster_payload(all_items_payload)
        custom_id = f"cluster_{cluster.id}"
        batch_requests.append(provider.build_cluster_request(
            custom_id=custom_id,
            items=dedup_items,
            categories=user_cats[uid],
            output_language=user_langs[uid],
        ))
        request_meta.append({
            "custom_id": custom_id,
            "item_id": str(cluster.id),
            "item_type": "cluster",
            "item_count": len(items),
            "dedup_item_count": len(dedup_items),
            "orig_to_dedup": orig_to_dedup,
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
    n_groups = sum(1 for m in request_meta if m["item_type"] == "news_item_group")
    n_clusters = sum(1 for m in request_meta if m["item_type"] == "cluster")
    logger.info("Submitted batch %s: %d group requests, %d cluster requests", batch.id, n_groups, n_clusters)
    return llm_batch


def apply_batch_results(db: Session, llm_batch: LLMBatch, results, provider=None) -> set[str]:
    """Write LLM results to DB. Returns the set of successfully applied custom_ids."""
    meta_by_id = {r["custom_id"]: r for r in llm_batch.requests}
    applied: set[str] = set()
    provider_name = getattr(provider, "provider_name", "") or ""
    model_name = getattr(provider, "model_name", "") or ""

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
            if meta["item_type"] == "news_item_group":
                _apply_item_group_result(db, meta, text, provider_name, model_name)
            else:
                _apply_cluster_result(db, meta, text, provider_name, model_name)
            applied.add(cid)
        except Exception:
            logger.exception("Failed to apply result for %s", cid)

    db.commit()

    # Propagate LLM results to same-URL items for other users
    propagated = 0
    for cid in applied:
        meta = meta_by_id[cid]
        if meta["item_type"] == "news_item_group":
            for item_id in meta["item_ids"]:
                item = db.get(NewsItem, uuid.UUID(item_id) if isinstance(item_id, str) else item_id)
                if item and item.llm_processed:
                    propagated += propagate_llm_results(db, item)
    if propagated:
        db.commit()
        logger.debug("Batch: propagated LLM results to %d same-URL item(s) for other users", propagated)

    # Send push notifications for items/clusters processed in this batch
    try:
        from app.services.push_service import notify_item, notify_cluster
        from app.models import NewsCluster
        for cid in applied:
            meta = meta_by_id[cid]
            if meta["item_type"] == "news_item_group":
                for item_id in meta.get("item_ids", []):
                    item = db.get(NewsItem, item_id)
                    if item:
                        notify_item(db, item)
            elif meta["item_type"] == "cluster":
                import uuid as _uuid
                from sqlalchemy import select as _select
                cluster = db.get(NewsCluster, _uuid.UUID(meta["item_id"]))
                if cluster:
                    items = db.scalars(_select(NewsItem).where(NewsItem.cluster_id == cluster.id)).all()
                    notify_cluster(db, cluster, list(items))
    except Exception:
        logger.exception("Push notification dispatch failed after batch apply")

    return applied


def _apply_item_group_result(db: Session, meta: dict, text: str, provider_name: str = "", model_name: str = "") -> None:
    group_type = meta["group_type"]
    is_short = group_type == "short"
    is_social = group_type == "social"

    # All items in a group share the same user_id
    first_item = db.get(NewsItem, meta["item_ids"][0])
    if not first_item:
        return
    known = [c.name for c in db.scalars(
        select(Category).where(Category.user_id == first_item.user_id, Category.is_active == True)  # noqa: E712
    ).all()]

    results = parse_multi_item_response(text, known, is_short=is_short, is_social=is_social)

    for item_id in meta["item_ids"]:
        result = results.get(item_id)
        if not result:
            # LLM missed this item — fall back to individual sync processing
            from app.tasks.process_tasks import process_news_item
            process_news_item.apply_async(args=[item_id], queue="process")
            continue

        item = db.get(NewsItem, item_id)
        if not item or item.llm_processed:
            continue

        if is_short:
            item.abstract = item.raw_content or item.title
        elif is_social and result.generated_title:
            item.title = result.generated_title
            item.abstract = item.raw_content or ""
        else:
            item.abstract = result.abstract
            if result.generated_title:
                item.title = result.generated_title

        item.extracted_keywords = result.keywords or None
        item.relevance_score = result.relevance_score
        item.impact_score = result.impact_score
        item.llm_processed = True
        item.llm_provider = provider_name or None
        item.llm_model = model_name or None

        if result.category_names:
            cats = db.scalars(
                select(Category).where(
                    Category.name.in_(result.category_names),
                    Category.user_id == item.user_id,
                )
            ).all()
            item.categories = list(cats)


def _apply_cluster_result(db: Session, meta: dict, text: str, provider_name: str = "", model_name: str = "") -> None:
    cluster = db.get(NewsCluster, meta["item_id"])
    if not cluster or cluster.llm_processed:
        return

    known = [c.name for c in db.scalars(
        select(Category).where(Category.user_id == cluster.user_id, Category.is_active == True)  # noqa: E712
    ).all()]

    dedup_count = meta.get("dedup_item_count", meta.get("item_count", 0))
    result = parse_cluster_response(text, dedup_count, known)
    cluster.title = result.title
    cluster.unified_abstract = result.unified_abstract
    cluster.extracted_keywords = result.keywords or None
    cluster.relevance_score = result.relevance_score
    cluster.impact_score = result.impact_score
    cluster.llm_processed = True
    cluster.llm_provider = provider_name or None
    cluster.llm_model = model_name or None

    if result.category_names:
        cats = db.scalars(
            select(Category).where(
                Category.name.in_(result.category_names),
                Category.user_id == cluster.user_id,
            )
        ).all()
        cluster.categories = list(cats)

    items = db.scalars(select(NewsItem).where(NewsItem.cluster_id == cluster.id)).all()
    orig_to_dedup: list[int | None] = meta.get("orig_to_dedup") or list(range(len(items)))
    for i, item in enumerate(items):
        dedup_idx = orig_to_dedup[i] if i < len(orig_to_dedup) else i
        item.source_summary = result.source_summaries.get(f"item_{dedup_idx}", "") if dedup_idx is not None else ""
        item.llm_processed = True
