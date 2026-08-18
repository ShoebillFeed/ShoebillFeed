import uuid
from datetime import datetime, timedelta, timezone

from app.models.category import Category
from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem
from app.models.source import Source


def _make_source(db_session, user_id, name="Feed"):
    source = Source(user_id=user_id, name=name, source_type="rss", config={"url": f"https://example.com/{name}"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_category(db_session, user_id, name="Tech", color="#6366f1"):
    cat = Category(user_id=user_id, name=name, color=color, keywords=[])
    db_session.add(cat)
    db_session.flush()
    return cat


def _make_item(db_session, source, user_id, *, keywords, fetched_at, categories=None):
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
    if categories:
        item.categories = categories
    db_session.add(item)
    db_session.flush()
    return item


def _make_n(db_session, source, user_id, n, *, keywords, fetched_at, categories=None):
    for _ in range(n):
        _make_item(db_session, source, user_id, keywords=keywords, fetched_at=fetched_at, categories=categories)


def _make_cluster(db_session, user_id, source, *, keywords, categories=None, created_at=None):
    cluster = NewsCluster(user_id=user_id, title="Cluster", extracted_keywords=keywords)
    if categories:
        cluster.categories = categories
    if created_at:
        cluster.created_at = created_at
    db_session.add(cluster)
    db_session.flush()
    for _ in range(2):
        db_session.add(NewsItem(
            source_id=source.id, user_id=user_id, cluster_id=cluster.id,
            title="member", url=f"https://example.com/{uuid.uuid4().hex}", url_hash=f"hash-{uuid.uuid4().hex}",
        ))
    db_session.flush()
    return cluster


def _get(client, **params):
    return client.get("/api/stats/keyword-momentum", params=params)


def _find(body, keyword):
    return next((r for r in body if r["keyword"] == keyword), None)


class TestKeywordMomentumRising:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/keyword-momentum")
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
        assert entry["is_dormant"] is False

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

    def test_filters_by_category(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        world = _make_category(db_session, user.id, name="World")
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 5, keywords=["only tech"], fetched_at=now, categories=[tech])
        _make_n(db_session, source, user.id, 5, keywords=["only world"], fetched_at=now, categories=[world])
        db_session.commit()

        resp = _get(auth_client, category_ids=[str(tech.id)])
        body = resp.json()
        assert _find(body, "only tech") is not None
        assert _find(body, "only world") is None

    def test_category_filter_also_applies_to_clusters(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        world = _make_category(db_session, user.id, name="World")
        now = datetime.now(timezone.utc)
        for _ in range(5):
            _make_cluster(db_session, user.id, source, keywords=["cluster tech term"], categories=[tech], created_at=now)
        for _ in range(5):
            _make_cluster(db_session, user.id, source, keywords=["cluster world term"], categories=[world], created_at=now)
        db_session.commit()

        resp = _get(auth_client, category_ids=[str(tech.id)])
        body = resp.json()
        assert _find(body, "cluster tech term") is not None
        assert _find(body, "cluster world term") is None

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

    def test_default_direction_excludes_a_purely_declining_keyword(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        # Decline entirely in the older months, tapering to zero for the two
        # most recent ones (which overlap the 8-week/56-day weekly window) --
        # a nonzero point in the most recent week would otherwise give this
        # keyword an artificial *positive* weekly slope (a fresh mention
        # after a long gap looks like a spike to an 8-point OLS fit), which
        # would make it eligible for "rising" via the max(weekly, monthly)
        # inclusion rule even though the monthly trend is purely negative --
        # not what this test means to exercise.
        for months_ago, count in [(5, 6), (4, 5), (3, 4), (2, 3), (1, 0), (0, 0)]:
            _make_n(
                db_session, source, user.id, count,
                keywords=["fading fast"],
                fetched_at=now - timedelta(days=30 * months_ago + 1),
            )
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        assert _find(body, "fading fast") is None


class TestKeywordMomentumFalling:
    def test_surfaces_a_keyword_with_gradual_monthly_decline(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        # Roughly decreasing counts month over month.
        for months_ago, count in [(5, 6), (4, 5), (3, 4), (2, 3), (1, 2), (0, 1)]:
            _make_n(
                db_session, source, user.id, count,
                keywords=["fading topic"],
                fetched_at=now - timedelta(days=30 * months_ago + 1),
            )
        db_session.commit()

        resp = _get(auth_client, direction="falling")
        assert resp.status_code == 200
        body = resp.json()
        entry = _find(body, "fading topic")
        assert entry is not None
        assert entry["monthly_slope"] < 0
        assert entry["total_mentions"] == 21

    def test_surfaces_a_keyword_with_a_recent_weekly_dropoff(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 6, keywords=["dropoff"], fetched_at=now - timedelta(weeks=7))
        _make_n(db_session, source, user.id, 1, keywords=["dropoff"], fetched_at=now)
        db_session.commit()

        resp = _get(auth_client, direction="falling")
        body = resp.json()
        entry = _find(body, "dropoff")
        assert entry is not None
        assert entry["weekly_slope"] < 0

    def test_flags_a_dormant_keyword(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_n(db_session, source, user.id, 5, keywords=["gone quiet"], fetched_at=now - timedelta(days=100))
        db_session.commit()

        resp = _get(auth_client, direction="falling")
        body = resp.json()
        entry = _find(body, "gone quiet")
        assert entry is not None
        assert entry["is_dormant"] is True
        assert entry["is_newcomer"] is False

    def test_does_not_flag_an_active_keyword_as_dormant(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        # Steadily declining but still mentioned in the most recent bucket --
        # a real decline (negative slope), just not gone quiet yet.
        for months_ago, count in [(5, 6), (4, 5), (3, 4), (2, 3), (1, 2), (0, 1)]:
            _make_n(
                db_session, source, user.id, count,
                keywords=["still active"],
                fetched_at=now - timedelta(days=30 * months_ago + 1),
            )
        db_session.commit()

        resp = _get(auth_client, direction="falling")
        body = resp.json()
        entry = _find(body, "still active")
        assert entry is not None
        assert entry["is_dormant"] is False

    def test_excludes_a_purely_growing_keyword(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        for months_ago, count in [(5, 1), (4, 2), (3, 3), (2, 4), (1, 5), (0, 6)]:
            _make_n(
                db_session, source, user.id, count,
                keywords=["growing fast"],
                fetched_at=now - timedelta(days=30 * months_ago + 1),
            )
        db_session.commit()

        resp = _get(auth_client, direction="falling")
        body = resp.json()
        assert _find(body, "growing fast") is None

    def test_filters_by_source(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        now = datetime.now(timezone.utc)
        _make_n(db_session, source_a, user.id, 6, keywords=["only a fading"], fetched_at=now - timedelta(weeks=7))
        _make_n(db_session, source_a, user.id, 1, keywords=["only a fading"], fetched_at=now)
        _make_n(db_session, source_b, user.id, 6, keywords=["only b fading"], fetched_at=now - timedelta(weeks=7))
        _make_n(db_session, source_b, user.id, 1, keywords=["only b fading"], fetched_at=now)
        db_session.commit()

        resp = _get(auth_client, direction="falling", source_ids=[str(source_a.id)])
        body = resp.json()
        assert _find(body, "only a fading") is not None
        assert _find(body, "only b fading") is None

    def test_rejects_an_invalid_direction(self, auth_client):
        resp = _get(auth_client, direction="sideways")
        assert resp.status_code == 422
