import uuid
from datetime import datetime, timedelta, timezone

from app.models.news_item import NewsItem
from app.models.source import Source


def _make_source(db_session, user_id, name="Feed"):
    source = Source(user_id=user_id, name=name, source_type="rss", config={"url": f"https://example.com/{name}"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_item(db_session, source, user_id, *, keywords, fetched_at):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=f"Article {unique}",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        extracted_keywords=keywords,
        fetched_at=fetched_at,
    )
    db_session.add(item)
    db_session.flush()
    return item


def _make_n(db_session, source, user_id, n, *, keywords, fetched_at):
    for _ in range(n):
        _make_item(db_session, source, user_id, keywords=keywords, fetched_at=fetched_at)


def _get(client, **params):
    return client.get("/api/stats/rising-keywords", params=params)


def _find(body, keyword):
    return next((r for r in body if r["keyword"] == keyword), None)


class TestRisingKeywords:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/rising-keywords")
        assert resp.status_code == 401

    def test_surfaces_a_keyword_with_gradual_monthly_growth(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        # Roughly increasing counts month over month -- a slow, sustained
        # climb a weekly window alone wouldn't clearly show.
        for months_ago, count in [(5, 1), (4, 2), (3, 3), (2, 4), (1, 5), (0, 6)]:
            _make_n(
                db_session, source, user.id, count,
                keywords=["quantum dot"],
                fetched_at=now - timedelta(days=30 * months_ago + 1),
            )
        db_session.commit()

        resp = _get(auth_client)
        assert resp.status_code == 200
        body = resp.json()
        entry = _find(body, "quantum dot")
        assert entry is not None
        assert entry["monthly_slope"] > 0
        assert entry["total_mentions"] == 21

    def test_surfaces_a_keyword_with_a_recent_weekly_spike(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 1, keywords=["chipgate"], fetched_at=now - timedelta(weeks=7))
        _make_n(db_session, source, user.id, 6, keywords=["chipgate"], fetched_at=now)
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        entry = _find(body, "chipgate")
        assert entry is not None
        assert entry["weekly_slope"] > 0

    def test_flags_a_newcomer_keyword(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 5, keywords=["brand new term"], fetched_at=now)
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        entry = _find(body, "brand new term")
        assert entry is not None
        assert entry["is_newcomer"] is True

    def test_does_not_flag_a_keyword_seen_in_an_earlier_month_as_newcomer(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 1, keywords=["established term"], fetched_at=now - timedelta(days=120))
        _make_n(db_session, source, user.id, 5, keywords=["established term"], fetched_at=now)
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        entry = _find(body, "established term")
        assert entry is not None
        assert entry["is_newcomer"] is False

    def test_excludes_keywords_below_the_minimum_mention_floor(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 1, keywords=["one off mention"], fetched_at=now)
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        assert _find(body, "one off mention") is None

    def test_is_case_insensitive(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 3, keywords=["Robotics"], fetched_at=now)
        _make_n(db_session, source, user.id, 3, keywords=["robotics"], fetched_at=now)
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        entry = _find(body, "robotics")
        assert entry is not None
        assert entry["total_mentions"] == 6

    def test_filters_by_source(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        now = datetime.now(timezone.utc)
        _make_n(db_session, source_a, user.id, 5, keywords=["only a"], fetched_at=now)
        _make_n(db_session, source_b, user.id, 5, keywords=["only b"], fetched_at=now)
        db_session.commit()

        resp = _get(auth_client, source_ids=[str(source_a.id)])
        body = resp.json()
        assert _find(body, "only a") is not None
        assert _find(body, "only b") is None

    def test_does_not_count_another_users_items(self, client, db_session, make_user):
        from app.services.auth import create_token

        owner = make_user(username="owner")
        other = make_user(username="other")
        source = _make_source(db_session, owner.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, owner.id, 5, keywords=["owners term"], fetched_at=now)
        db_session.commit()

        client.cookies.set("access_token", create_token(other.id, other.username))
        resp = _get(client)
        assert _find(resp.json(), "owners term") is None

    def test_excludes_mentions_outside_the_six_month_lookback(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 10, keywords=["ancient history"], fetched_at=now - timedelta(days=400))
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        assert _find(body, "ancient history") is None
