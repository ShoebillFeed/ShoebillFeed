import json
import logging
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.push_subscription import PushSubscription
from app.models.user_settings import UserSettings
from app.models.user_tab import UserTab
from app.models.news_item import NewsItem
from app.models.news_cluster import NewsCluster

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
    if not item.user_id:
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


def notify_cluster(db: Session, cluster: NewsCluster, items: list) -> None:
    if not cluster.user_id:
        return
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == cluster.user_id))
    if not s or not _cluster_eligible(s, cluster, items, db):
        return

    if s.push_cluster_per_source:
        allowed_sources = (
            {uuid.UUID(str(x)) for x in (s.push_source_ids or [])}
            if not s.push_all_sources else None
        )
        for item in items:
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
