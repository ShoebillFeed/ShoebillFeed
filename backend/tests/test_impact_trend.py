import uuid
from datetime import datetime, timedelta, timezone

from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem
from app.models.source import Source
from app.models.user_settings import UserSettings


def _make_source(db_session, user_id, name="Feed"):
    source = Source(user_id=user_id, name=name, source_type="rss", config={"url": f"https://example.com/{name}"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_item(db_session, source, user_id, *, impact_score=None, fetched_at=None, cluster_id=None):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=f"Article {unique}",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        impact_score=impact_score,
        fetched_at=fetched_at or datetime.now(timezone.utc),
        cluster_id=cluster_id,
    )
    db_session.add(item)
    db_session.flush()
    return item


def _make_cluster(db_session, user_id, *, impact_score=None, created_at=None):
    cluster = NewsCluster(user_id=user_id, title="Cluster", impact_score=impact_score)
    if created_at:
        cluster.created_at = created_at
    db_session.add(cluster)
    db_session.flush()
    return cluster


def _get(client, **params):
    return client.get("/api/stats/impact-trend", params=params)


class TestImpactTrend:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/impact-trend")
        assert resp.status_code == 401

    def test_computes_daily_average(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, impact_score=4)
        _make_item(db_session, source, user.id, impact_score=8)
        db_session.commit()

        resp = _get(auth_client)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["points"]) == 1
        point = body["points"][0]
        assert point["count"] == 2
        assert point["avg_impact"] == 6.0

    def test_counts_a_cluster_once_not_per_member(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        cluster = _make_cluster(db_session, user.id, impact_score=9)
        for _ in range(3):
            _make_item(db_session, source, user.id, cluster_id=cluster.id, impact_score=None)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["points"][0]["count"] == 1
        assert body["points"][0]["avg_impact"] == 9.0

    def test_default_high_impact_threshold_is_seven(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, impact_score=7)
        _make_item(db_session, source, user.id, impact_score=6)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["high_impact_threshold"] == 7
        assert body["points"][0]["high_impact_count"] == 1

    def test_respects_user_configured_threshold(self, auth_client, db_session):
        user = auth_client.current_user
        settings = UserSettings(user_id=user.id, push_min_relevance=9)
        db_session.add(settings)
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, impact_score=8)
        _make_item(db_session, source, user.id, impact_score=9)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["high_impact_threshold"] == 9
        assert body["points"][0]["high_impact_count"] == 1

    def test_excludes_items_without_an_impact_score(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, impact_score=None)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["points"] == []

    def test_filters_by_source(self, auth_client, db_session):
        user = auth_client.current_user
        wanted = _make_source(db_session, user.id, name="Wanted")
        other = _make_source(db_session, user.id, name="Other")
        _make_item(db_session, wanted, user.id, impact_score=5)
        _make_item(db_session, other, user.id, impact_score=10)
        db_session.commit()

        body = _get(auth_client, source_ids=[str(wanted.id)]).json()
        assert body["points"][0]["count"] == 1
        assert body["points"][0]["avg_impact"] == 5.0

    def test_source_filter_does_not_double_count_a_cluster_with_multiple_matching_members(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id, name="Wanted")
        cluster = _make_cluster(db_session, user.id, impact_score=10)
        for _ in range(2):
            _make_item(db_session, source, user.id, cluster_id=cluster.id, impact_score=None)
        db_session.commit()

        body = _get(auth_client, source_ids=[str(source.id)]).json()
        assert body["points"][0]["count"] == 1
        assert body["points"][0]["avg_impact"] == 10.0

    def test_respects_day_window(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, impact_score=3, fetched_at=now - timedelta(days=100))
        _make_item(db_session, source, user.id, impact_score=7, fetched_at=now - timedelta(days=1))
        db_session.commit()

        body = _get(auth_client, days=30).json()
        assert body["points"][0]["count"] == 1
        assert body["points"][0]["avg_impact"] == 7.0

    def test_does_not_count_another_users_items(self, auth_client, db_session, make_user):
        other = make_user(username="other")
        other_source = _make_source(db_session, other.id, name="OtherSource")
        _make_item(db_session, other_source, other.id, impact_score=10)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["points"] == []
