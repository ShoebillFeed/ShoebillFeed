import json
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.push_subscription import PushSubscription
from app.models.user_settings import UserSettings
from app.models.news_item import NewsItem
from app.models.news_cluster import NewsCluster

logger = logging.getLogger(__name__)


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


def _item_eligible(s: UserSettings, item: NewsItem) -> bool:
    if not s.push_enabled:
        return False
    if (item.relevance_score or 0) < s.push_min_relevance:
        return False
    if not s.push_all_sources:
        allowed = {str(x) for x in (s.push_source_ids or [])}
        if str(item.source_id) not in allowed:
            return False
    if not s.push_all_categories:
        allowed = {str(x) for x in (s.push_category_ids or [])}
        item_cats = {str(c.id) for c in (item.categories or [])}
        if not allowed & item_cats:
            return False
    return True


def notify_item(db: Session, item: NewsItem) -> None:
    if not item.user_id:
        return
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == item.user_id))
    if not s or not _item_eligible(s, item):
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
    if not s or not s.push_enabled:
        return
    if (cluster.relevance_score or 0) < s.push_min_relevance:
        return

    if not s.push_all_sources:
        allowed_sources = {str(x) for x in (s.push_source_ids or [])}
        cluster_sources = {str(i.source_id) for i in items if i.source_id}
        if not allowed_sources & cluster_sources:
            return

    if not s.push_all_categories:
        allowed_cats = {str(x) for x in (s.push_category_ids or [])}
        cluster_cats = {str(c.id) for c in (cluster.categories or [])}
        if not allowed_cats & cluster_cats:
            return

    if s.push_cluster_per_source:
        allowed_sources = {str(x) for x in (s.push_source_ids or [])} if not s.push_all_sources else None
        for item in items:
            if allowed_sources and str(item.source_id) not in allowed_sources:
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
