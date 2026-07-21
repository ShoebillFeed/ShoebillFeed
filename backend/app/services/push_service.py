import json
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.push_subscription import PushSubscription
from app.models.user_settings import UserSettings
from app.models.user_tab import UserTab
from app.models.news_item import NewsItem
from app.models.news_cluster import NewsCluster
from app.models.category import Category
from app.models.category_weight import CategoryWeight

logger = logging.getLogger(__name__)

# Virtual tab identifiers for the two built-in ranked tabs
_RELEVANT = "relevant"
_IMPACT = "impact"


def _send_to_subscription(sub: PushSubscription, payload: dict) -> bool:
    from app.config import get_settings
    settings = get_settings()
    if not settings.vapid_private_key or not settings.vapid_public_key:
        return False
    try:
        from pywebpush import webpush
        webpush(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
            content_encoding="aes128gcm",
        )
        return True
    except Exception as exc:
        logger.warning("Push send failed for %s…: %s", sub.endpoint[:50], exc)
        return False


def _dispatch(db: Session, user_id, payload: dict) -> None:
    subs = db.scalars(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    ).all()
    for sub in subs:
        _send_to_subscription(sub, payload)


def _category_allowed(s: UserSettings, categories) -> bool:
    """Global category filter: True if the user hasn't restricted notifications
    to specific categories, or if `categories` includes one of the allowed ones."""
    if s.push_all_categories:
        return True
    allowed = {uuid.UUID(str(cid)) for cid in (s.push_category_ids or [])}
    if not allowed:
        return False
    item_cats = {c.id for c in (categories or [])}
    return bool(allowed & item_cats)


def _source_allowed(s: UserSettings, source_ids) -> bool:
    """Global source filter: True if the user hasn't restricted notifications
    to specific sources, or if `source_ids` (a single UUID or iterable of UUIDs)
    includes one of the allowed ones."""
    if s.push_all_sources:
        return True
    allowed = {uuid.UUID(str(sid)) for sid in (s.push_source_ids or [])}
    if not allowed:
        return False
    if isinstance(source_ids, uuid.UUID):
        source_ids = {source_ids}
    return bool(allowed & set(source_ids))


def _category_percentile_allowed(s: UserSettings, categories, db: Session) -> bool:
    """Top-X% category filter: an item/cluster passes if at least one of its
    categories ranks among the user's top `push_top_category_percent` percent
    of categories by learned weight (weight * manual_weight). Categories
    without any learned weight yet use the neutral baseline of 1.0."""
    percent = s.push_top_category_percent
    if percent is None or percent >= 100:
        return True
    if percent <= 0:
        return False

    rows = db.execute(
        select(Category.id, CategoryWeight.weight, CategoryWeight.manual_weight)
        .outerjoin(CategoryWeight, CategoryWeight.category_id == Category.id)
        .where(Category.user_id == s.user_id, Category.is_active == True)  # noqa: E712
    ).all()
    if not rows:
        return False

    weight_map = {row.id: (row.weight or 1.0) * (row.manual_weight or 1.0) for row in rows}
    cutoff = max(1, math.ceil(len(weight_map) * percent / 100))
    threshold = sorted(weight_map.values(), reverse=True)[cutoff - 1]

    cat_ids = {c.id for c in (categories or [])}
    if not cat_ids:
        return 1.0 >= threshold
    effective = max((weight_map.get(cid, 1.0) for cid in cat_ids), default=1.0)
    return effective >= threshold


def _tab_matches_item(tab: UserTab, item: NewsItem, min_score: int) -> bool:
    """Return True if item would appear in the given custom tab at the threshold."""
    if tab.sort == "newest":
        return False
    score = item.impact_score if tab.sort == "impact" else item.relevance_score
    if (score or 0) < min_score:
        return False
    if tab.category_ids:
        item_cats = {c.id for c in (item.categories or [])}
        if not {uuid.UUID(str(cid)) for cid in tab.category_ids} & item_cats:
            return False
    if tab.source_ids:
        if item.source_id not in {uuid.UUID(str(sid)) for sid in tab.source_ids}:
            return False
    return True


def _item_eligible(s: UserSettings, item: NewsItem, db: Session) -> bool:
    if not s.push_enabled:
        return False
    if not _category_allowed(s, item.categories):
        return False
    if not _source_allowed(s, item.source_id):
        return False
    if not _category_percentile_allowed(s, item.categories, db):
        return False

    selected = [str(x) for x in (s.push_tab_ids or [])] if not s.push_all_tabs else None

    # push_all_tabs → behave like the old default: relevant score threshold only
    if selected is None:
        return (item.relevance_score or 0) >= s.push_min_relevance

    if not selected:
        return False

    for tab_id in selected:
        if tab_id == _RELEVANT:
            if (item.relevance_score or 0) >= s.push_min_relevance:
                return True
        elif tab_id == _IMPACT:
            if (item.impact_score or 0) >= s.push_min_relevance:
                return True
        else:
            try:
                tab = db.get(UserTab, uuid.UUID(tab_id))
            except (ValueError, AttributeError):
                continue
            if tab and tab.user_id == item.user_id and _tab_matches_item(tab, item, s.push_min_relevance):
                return True

    return False


def _cluster_eligible(s: UserSettings, cluster: NewsCluster, items: list, db: Session) -> bool:
    if not s.push_enabled:
        return False
    if not _category_allowed(s, cluster.categories):
        return False
    if not _source_allowed(s, {i.source_id for i in items if i.source_id}):
        return False
    if not _category_percentile_allowed(s, cluster.categories, db):
        return False

    selected = [str(x) for x in (s.push_tab_ids or [])] if not s.push_all_tabs else None

    if selected is None:
        return (cluster.relevance_score or 0) >= s.push_min_relevance

    if not selected:
        return False

    for tab_id in selected:
        if tab_id == _RELEVANT:
            if (cluster.relevance_score or 0) >= s.push_min_relevance:
                return True
        elif tab_id == _IMPACT:
            if (cluster.impact_score or 0) >= s.push_min_relevance:
                return True
        else:
            try:
                tab = db.get(UserTab, uuid.UUID(tab_id))
            except (ValueError, AttributeError):
                continue
            if not tab or tab.sort == "newest":
                continue
            score = cluster.impact_score if tab.sort == "impact" else cluster.relevance_score
            if (score or 0) < s.push_min_relevance:
                continue
            if tab.category_ids:
                cluster_cats = {c.id for c in (cluster.categories or [])}
                if not {uuid.UUID(str(cid)) for cid in tab.category_ids} & cluster_cats:
                    continue
            if tab.source_ids:
                cluster_sources = {i.source_id for i in items if i.source_id}
                if not {uuid.UUID(str(sid)) for sid in tab.source_ids} & cluster_sources:
                    continue
            return True

    return False


def notify_item(db: Session, item: NewsItem) -> None:
    if not item.user_id or item.notified_at is not None:
        return
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == item.user_id))
    if not s or not _item_eligible(s, item, db):
        return
    payload = {
        "title": item.title,
        "body": (item.abstract or "")[:120],
        "url": item.url,
        "tag": f"item-{item.id}",
    }
    _dispatch(db, item.user_id, payload)
    item.notified_at = datetime.now(timezone.utc)
    db.commit()


def notify_cluster(db: Session, cluster: NewsCluster, items: list) -> None:
    if not cluster.user_id:
        return

    # Items already individually notified (or covered by an earlier cluster
    # notification) shouldn't trigger another push when the cluster is
    # reprocessed after gaining new members.
    pending = [i for i in items if i.notified_at is None]
    if not pending:
        return

    s = db.scalar(select(UserSettings).where(UserSettings.user_id == cluster.user_id))
    if not s or not _cluster_eligible(s, cluster, items, db):
        return

    if s.push_cluster_per_source:
        allowed_sources = (
            {uuid.UUID(str(x)) for x in (s.push_source_ids or [])}
            if not s.push_all_sources else None
        )
        for item in pending:
            if allowed_sources and item.source_id not in allowed_sources:
                continue
            source_name = item.source.name if item.source else "Unknown"
            payload = {
                "title": cluster.title or item.title,
                "body": f"{source_name}: {(item.source_summary or item.title)[:100]}",
                "url": item.url,
                "tag": f"cluster-item-{item.id}",
            }
            _dispatch(db, cluster.user_id, payload)
    else:
        source_names = ", ".join(sorted({i.source.name for i in items if i.source}))[:60]
        body = f"{source_names} — {(cluster.unified_abstract or '')[:100]}" if source_names else (cluster.unified_abstract or "")[:120]
        payload = {
            "title": cluster.title or "Multiple sources",
            "body": body,
            "url": "/",
            "tag": f"cluster-{cluster.id}",
        }
        _dispatch(db, cluster.user_id, payload)

    now = datetime.now(timezone.utc)
    for item in pending:
        item.notified_at = now
    db.commit()


def count_recent_matches(db: Session, user_id, days: int) -> int:
    """How many recently-fetched items/clusters would have been eligible for
    a notification under the user's *current* settings. Used for the settings
    page preview so filter changes are checked against real recent data
    instead of taken on faith. Approximate, not an exact replay of dispatch:
    counts one match per eligible cluster regardless of push_cluster_per_source,
    and doesn't account for items already notified."""
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
    if not s or not s.push_enabled:
        return 0

    since = datetime.now(timezone.utc) - timedelta(days=days)

    standalone_items = db.scalars(
        select(NewsItem).where(
            NewsItem.user_id == user_id,
            NewsItem.cluster_id.is_(None),
            NewsItem.fetched_at >= since,
        )
    ).all()
    count = sum(1 for item in standalone_items if _item_eligible(s, item, db))

    clusters = db.scalars(
        select(NewsCluster)
        .options(selectinload(NewsCluster.items))
        .where(NewsCluster.user_id == user_id, NewsCluster.created_at >= since)
    ).all()
    count += sum(1 for cluster in clusters if _cluster_eligible(s, cluster, cluster.items, db))

    return count
