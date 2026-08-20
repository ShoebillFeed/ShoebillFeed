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


def _make_item(db_session, source, user_id, *, read_later=False, is_read=False, fetched_at=None):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=f"Article {unique}",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        read_later=read_later,
        is_read=is_read,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.flush()
    return item


def _make_cluster(db_session, user_id, *, read_later=False, is_read=False, created_at=None):
    cluster = NewsCluster(user_id=user_id, title="Cluster", read_later=read_later, is_read=is_read)
    if created_at:
        cluster.created_at = created_at
    db_session.add(cluster)
    db_session.flush()
    return cluster


def _get(client):
    return client.get("/api/stats/read-later-backlog")


def _bucket(body, key):
    return next(b for b in body["buckets"] if b["key"] == key)


class TestReadLaterBacklog:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/read-later-backlog")
        assert resp.status_code == 401

    def test_empty_backlog(self, auth_client, db_session):
        resp = _get(auth_client)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["oldest_days"] is None
        assert all(b["count"] == 0 for b in body["buckets"])

    def test_counts_unread_saved_items(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, read_later=True, is_read=False)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["total"] == 1

    def test_excludes_items_not_saved(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, read_later=False, is_read=False)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["total"] == 0

    def test_excludes_saved_items_already_read(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, read_later=True, is_read=True)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["total"] == 0

    def test_counts_a_saved_cluster(self, auth_client, db_session):
        user = auth_client.current_user
        _make_cluster(db_session, user.id, read_later=True, is_read=False)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["total"] == 1

    def test_buckets_by_age(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, read_later=True, fetched_at=now - timedelta(hours=2))
        _make_item(db_session, source, user.id, read_later=True, fetched_at=now - timedelta(days=2))
        _make_item(db_session, source, user.id, read_later=True, fetched_at=now - timedelta(days=45))
        db_session.commit()

        body = _get(auth_client).json()
        assert body["total"] == 3
        assert _bucket(body, "under_1d")["count"] == 1
        assert _bucket(body, "1_3d")["count"] == 1
        assert _bucket(body, "over_30d")["count"] == 1
        assert body["oldest_days"] > 44

    def test_does_not_count_another_users_items(self, auth_client, db_session, make_user):
        other = make_user(username="other")
        other_source = _make_source(db_session, other.id, name="OtherSource")
        _make_item(db_session, other_source, other.id, read_later=True)
        db_session.commit()

        body = _get(auth_client).json()
        assert body["total"] == 0
