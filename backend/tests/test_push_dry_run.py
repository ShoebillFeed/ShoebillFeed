import uuid
from datetime import datetime, timedelta, timezone

from app.models.category import Category
from app.models.news_item import NewsItem
from app.models.source import Source
from app.models.user_settings import UserSettings
from app.services.push_service import count_recent_matches


def _make_category(db_session, user_id, name="Tech"):
    cat = Category(user_id=user_id, name=name, keywords=[])
    db_session.add(cat)
    db_session.flush()
    return cat


def _make_source(db_session, user_id):
    source = Source(user_id=user_id, name="Feed", source_type="rss", config={"url": "https://example.com/feed"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_item(db_session, source, user_id, category=None, relevance_score=8, days_ago=1):
    unique = uuid.uuid4()
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title="An article",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        relevance_score=relevance_score,
        fetched_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )
    if category:
        item.categories = [category]
    db_session.add(item)
    db_session.flush()
    return item


def test_no_settings_row_means_zero(db_session, make_user):
    user = make_user()
    assert count_recent_matches(db_session, user.id, days=7) == 0


def test_push_disabled_means_zero(db_session, make_user):
    user = make_user()
    db_session.add(UserSettings(user_id=user.id, push_enabled=False))
    db_session.flush()
    source = _make_source(db_session, user.id)
    _make_item(db_session, source, user.id, relevance_score=10)

    assert count_recent_matches(db_session, user.id, days=7) == 0


def test_counts_items_meeting_the_relevance_threshold(db_session, make_user):
    user = make_user()
    db_session.add(UserSettings(user_id=user.id, push_enabled=True, push_min_relevance=7))
    db_session.flush()
    source = _make_source(db_session, user.id)
    _make_item(db_session, source, user.id, relevance_score=9)
    _make_item(db_session, source, user.id, relevance_score=8)
    _make_item(db_session, source, user.id, relevance_score=3)  # below threshold

    assert count_recent_matches(db_session, user.id, days=7) == 2


def test_ignores_items_outside_the_day_window(db_session, make_user):
    user = make_user()
    db_session.add(UserSettings(user_id=user.id, push_enabled=True, push_min_relevance=1))
    db_session.flush()
    source = _make_source(db_session, user.id)
    _make_item(db_session, source, user.id, relevance_score=10, days_ago=1)
    _make_item(db_session, source, user.id, relevance_score=10, days_ago=30)  # outside a 7-day window

    assert count_recent_matches(db_session, user.id, days=7) == 1


def test_category_restriction_excludes_non_matching_items(db_session, make_user):
    user = make_user()
    wanted = _make_category(db_session, user.id, "Wanted")
    other = _make_category(db_session, user.id, "Other")
    db_session.add(UserSettings(
        user_id=user.id, push_enabled=True, push_min_relevance=1,
        push_all_categories=False, push_category_ids=[str(wanted.id)],
    ))
    db_session.flush()
    source = _make_source(db_session, user.id)
    _make_item(db_session, source, user.id, category=wanted, relevance_score=9)
    _make_item(db_session, source, user.id, category=other, relevance_score=9)

    assert count_recent_matches(db_session, user.id, days=7) == 1


def test_dry_run_endpoint(auth_client, db_session):
    user = auth_client.current_user
    db_session.add(UserSettings(user_id=user.id, push_enabled=True, push_min_relevance=1))
    db_session.flush()
    source = _make_source(db_session, user.id)
    _make_item(db_session, source, user.id, relevance_score=9)

    resp = auth_client.get("/api/push/dry-run", params={"days": 7})
    assert resp.status_code == 200
    assert resp.json() == {"count": 1, "days": 7}
