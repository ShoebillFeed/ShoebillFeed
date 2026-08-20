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


def _make_category(db_session, user_id, name="Tech", color="#6366f1", is_active=True):
    cat = Category(user_id=user_id, name=name, color=color, keywords=[], is_active=is_active)
    db_session.add(cat)
    db_session.flush()
    return cat


def _make_item(db_session, source, user_id, *, categories=None, fetched_at=None):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=f"Article {unique}",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )
    if categories:
        item.categories = categories
    db_session.add(item)
    db_session.flush()
    return item


def _make_cluster(db_session, user_id, sources, *, categories=None, created_at=None):
    cluster = NewsCluster(user_id=user_id, title="Cluster")
    if categories:
        cluster.categories = categories
    if created_at:
        cluster.created_at = created_at
    db_session.add(cluster)
    db_session.flush()
    for source in sources:
        db_session.add(NewsItem(
            source_id=source.id, user_id=user_id, cluster_id=cluster.id,
            title="member", url=f"https://example.com/{uuid.uuid4().hex}", url_hash=f"hash-{uuid.uuid4().hex}",
        ))
    db_session.flush()
    return cluster


def _get(client, **params):
    return client.get("/api/stats/category-trend", params=params)


class TestCategoryTrend:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/category-trend")
        assert resp.status_code == 401

    def test_counts_a_matching_news_item(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        _make_item(db_session, source, user.id, categories=[tech])
        db_session.commit()

        resp = _get(auth_client)
        assert resp.status_code == 200
        body = resp.json()
        tech_result = next(r for r in body["categories"] if r["name"] == "Tech")
        assert sum(p["count"] for p in tech_result["points"]) == 1

    def test_counts_a_matching_news_cluster_once_not_per_member(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        tech = _make_category(db_session, user.id, name="Tech")
        _make_cluster(db_session, user.id, [source_a, source_b], categories=[tech])
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        tech_result = next(r for r in body["categories"] if r["name"] == "Tech")
        assert sum(p["count"] for p in tech_result["points"]) == 1

    def test_tracks_multiple_categories_independently(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        world = _make_category(db_session, user.id, name="World")
        _make_item(db_session, source, user.id, categories=[tech])
        _make_item(db_session, source, user.id, categories=[tech])
        _make_item(db_session, source, user.id, categories=[world])
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        by_name = {r["name"]: sum(p["count"] for p in r["points"]) for r in body["categories"]}
        assert by_name["Tech"] == 2
        assert by_name["World"] == 1

    def test_filters_by_source(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        tech = _make_category(db_session, user.id, name="Tech")
        _make_item(db_session, source_a, user.id, categories=[tech])
        _make_item(db_session, source_b, user.id, categories=[tech])
        db_session.commit()

        resp = _get(auth_client, source_ids=[str(source_a.id)])
        body = resp.json()
        tech_result = next(r for r in body["categories"] if r["name"] == "Tech")
        assert sum(p["count"] for p in tech_result["points"]) == 1

    def test_cluster_source_filter_matches_any_member_source(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        tech = _make_category(db_session, user.id, name="Tech")
        _make_cluster(db_session, user.id, [source_a, source_b], categories=[tech])
        db_session.commit()

        resp = _get(auth_client, source_ids=[str(source_b.id)])
        body = resp.json()
        tech_result = next(r for r in body["categories"] if r["name"] == "Tech")
        assert sum(p["count"] for p in tech_result["points"]) == 1

    def test_excludes_items_outside_the_day_window(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, categories=[tech], fetched_at=now - timedelta(days=100))
        _make_item(db_session, source, user.id, categories=[tech], fetched_at=now - timedelta(days=1))
        db_session.commit()

        resp = _get(auth_client, days=30)
        body = resp.json()
        tech_result = next(r for r in body["categories"] if r["name"] == "Tech")
        assert sum(p["count"] for p in tech_result["points"]) == 1

    def test_accepts_the_full_365_day_window(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, categories=[tech], fetched_at=now - timedelta(days=300))
        db_session.commit()

        resp = _get(auth_client, days=365)
        assert resp.status_code == 200
        body = resp.json()
        tech_result = next(r for r in body["categories"] if r["name"] == "Tech")
        assert sum(p["count"] for p in tech_result["points"]) == 1

    def test_includes_an_uncategorized_bucket(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, categories=[])
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        uncategorized = next((r for r in body["categories"] if r["id"] == "uncategorized"), None)
        assert uncategorized is not None
        assert sum(p["count"] for p in uncategorized["points"]) == 1

    def test_excludes_inactive_categories(self, auth_client, db_session):
        user = auth_client.current_user
        _make_category(db_session, user.id, name="Retired", is_active=False)
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        assert all(r["name"] != "Retired" for r in body["categories"])

    def test_does_not_count_another_users_items(self, client, db_session, make_user):
        from app.services.auth import create_token

        owner = make_user(username="owner")
        other = make_user(username="other")
        source = _make_source(db_session, owner.id)
        tech = _make_category(db_session, owner.id, name="Tech")
        _make_item(db_session, source, owner.id, categories=[tech])
        db_session.commit()

        client.cookies.set("access_token", create_token(other.id, other.username))
        resp = _get(client)
        body = resp.json()
        assert body["categories"] == []
        assert body["totals"] == []

    def test_rejects_a_day_window_beyond_the_hard_cap(self, auth_client):
        resp = _get(auth_client, days=99999)
        assert resp.status_code == 422


class TestCategoryTrendTotals:
    def test_totals_count_every_article_once_regardless_of_category(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        world = _make_category(db_session, user.id, name="World")
        _make_item(db_session, source, user.id, categories=[tech])
        _make_item(db_session, source, user.id, categories=[world])
        _make_item(db_session, source, user.id, categories=[])
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        assert sum(p["count"] for p in body["totals"]) == 3

    def test_totals_count_a_multi_category_article_only_once(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        world = _make_category(db_session, user.id, name="World")
        # One article in two categories -- would double-count if totals were
        # derived by summing the per-category series client-side.
        _make_item(db_session, source, user.id, categories=[tech, world])
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        by_name = {r["name"]: sum(p["count"] for p in r["points"]) for r in body["categories"]}
        assert by_name["Tech"] == 1
        assert by_name["World"] == 1
        assert sum(p["count"] for p in body["totals"]) == 1

    def test_totals_count_a_cluster_once_not_per_member(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        tech = _make_category(db_session, user.id, name="Tech")
        _make_cluster(db_session, user.id, [source_a, source_b], categories=[tech])
        db_session.commit()

        resp = _get(auth_client)
        body = resp.json()
        assert sum(p["count"] for p in body["totals"]) == 1

    def test_totals_respect_the_source_filter(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        _make_item(db_session, source_a, user.id, categories=[])
        _make_item(db_session, source_b, user.id, categories=[])
        db_session.commit()

        resp = _get(auth_client, source_ids=[str(source_a.id)])
        body = resp.json()
        assert sum(p["count"] for p in body["totals"]) == 1

    def test_totals_respect_the_day_window(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, categories=[], fetched_at=now - timedelta(days=100))
        _make_item(db_session, source, user.id, categories=[], fetched_at=now - timedelta(days=1))
        db_session.commit()

        resp = _get(auth_client, days=30)
        body = resp.json()
        assert sum(p["count"] for p in body["totals"]) == 1
