import uuid
from datetime import datetime, timedelta, timezone

from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem
from app.models.source import Source


def _make_source(db_session, user_id, name="Feed"):
    source = Source(user_id=user_id, name=name, source_type="rss", config={"url": f"https://example.com/{name}"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_item(db_session, source, user_id, *, relevance_score=None, is_relevant=False, fetched_at=None, cluster_id=None):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=f"Article {unique}",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        relevance_score=relevance_score,
        is_relevant=is_relevant,
        fetched_at=fetched_at or datetime.now(timezone.utc),
        cluster_id=cluster_id,
    )
    db_session.add(item)
    db_session.flush()
    return item


def _make_cluster(db_session, user_id, *, relevance_score=None, is_relevant=False, created_at=None):
    cluster = NewsCluster(
        user_id=user_id, title="Cluster", relevance_score=relevance_score, is_relevant=is_relevant,
    )
    if created_at:
        cluster.created_at = created_at
    db_session.add(cluster)
    db_session.flush()
    return cluster


def _get(client, **params):
    return client.get("/api/stats/relevance-calibration", params=params)


def _bucket(body, score):
    return next(b for b in body if b["score"] == score)


class TestRelevanceCalibration:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/relevance-calibration")
        assert resp.status_code == 401

    def test_always_returns_all_ten_buckets(self, auth_client, db_session):
        resp = _get(auth_client)
        assert resp.status_code == 200
        body = resp.json()
        assert sorted(b["score"] for b in body) == list(range(1, 11))
        for b in body:
            assert b["count"] == 0
            assert b["relevant_rate"] is None

    def test_computes_relevant_rate_for_a_bucket(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, relevance_score=8, is_relevant=True)
        _make_item(db_session, source, user.id, relevance_score=8, is_relevant=True)
        _make_item(db_session, source, user.id, relevance_score=8, is_relevant=False)
        db_session.commit()

        body = _get(auth_client).json()
        b8 = _bucket(body, 8)
        assert b8["count"] == 3
        assert b8["relevant_count"] == 2
        assert b8["relevant_rate"] == 2 / 3

    def test_counts_a_cluster_once_not_per_member(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        cluster = _make_cluster(db_session, user.id, relevance_score=5, is_relevant=True)
        for _ in range(3):
            _make_item(db_session, source, user.id, cluster_id=cluster.id, relevance_score=None)
        db_session.commit()

        body = _get(auth_client).json()
        b5 = _bucket(body, 5)
        assert b5["count"] == 1
        assert b5["relevant_count"] == 1

    def test_excludes_items_without_a_relevance_score(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, relevance_score=None)
        db_session.commit()

        body = _get(auth_client).json()
        assert all(b["count"] == 0 for b in body)

    def test_respects_day_window(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, relevance_score=6, fetched_at=now - timedelta(days=200))
        _make_item(db_session, source, user.id, relevance_score=6, fetched_at=now - timedelta(days=1))
        db_session.commit()

        body = _get(auth_client, days=90).json()
        assert _bucket(body, 6)["count"] == 1

    def test_does_not_count_another_users_items(self, auth_client, db_session, make_user):
        other = make_user(username="other")
        other_source = _make_source(db_session, other.id, name="OtherSource")
        _make_item(db_session, other_source, other.id, relevance_score=9, is_relevant=True)
        db_session.commit()

        body = _get(auth_client).json()
        assert all(b["count"] == 0 for b in body)
