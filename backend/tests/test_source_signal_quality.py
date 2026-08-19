import uuid
from datetime import datetime, timedelta, timezone

from app.models.news_item import NewsItem
from app.models.source import Source


def _make_source(db_session, user_id, name="Feed"):
    source = Source(user_id=user_id, name=name, source_type="rss", config={"url": f"https://example.com/{name}"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_item(db_session, source, user_id, *, is_relevant=False, is_disliked=False, is_read=False, fetched_at=None):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=f"Article {unique}",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        is_relevant=is_relevant,
        is_disliked=is_disliked,
        is_read=is_read,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.flush()
    return item


def _get(client, **params):
    return client.get("/api/stats/source-signal-quality", params=params)


class TestSourceSignalQuality:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/source-signal-quality")
        assert resp.status_code == 401

    def test_counts_relevant_disliked_read_per_source(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, is_relevant=True, is_read=True)
        _make_item(db_session, source, user.id, is_disliked=True, is_read=True)
        _make_item(db_session, source, user.id)
        db_session.commit()

        resp = _get(auth_client)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        row = body[0]
        assert row["total"] == 3
        assert row["relevant"] == 1
        assert row["disliked"] == 1
        assert row["read"] == 2

    def test_separates_sources(self, auth_client, db_session):
        user = auth_client.current_user
        good = _make_source(db_session, user.id, name="Good")
        bad = _make_source(db_session, user.id, name="Bad")
        _make_item(db_session, good, user.id, is_relevant=True)
        _make_item(db_session, good, user.id, is_relevant=True)
        _make_item(db_session, bad, user.id, is_disliked=True)
        db_session.commit()

        resp = _get(auth_client)
        by_name = {r["name"]: r for r in resp.json()}
        assert by_name["Good"]["relevant"] == 2
        assert by_name["Good"]["disliked"] == 0
        assert by_name["Bad"]["disliked"] == 1

    def test_sorted_by_total_descending(self, auth_client, db_session):
        user = auth_client.current_user
        small = _make_source(db_session, user.id, name="Small")
        big = _make_source(db_session, user.id, name="Big")
        _make_item(db_session, small, user.id)
        for _ in range(3):
            _make_item(db_session, big, user.id)
        db_session.commit()

        resp = _get(auth_client)
        names = [r["name"] for r in resp.json()]
        assert names == ["Big", "Small"]

    def test_respects_day_window(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, fetched_at=now - timedelta(days=100))
        _make_item(db_session, source, user.id, fetched_at=now - timedelta(days=1))
        db_session.commit()

        resp = _get(auth_client, days=30)
        assert resp.json()[0]["total"] == 1

    def test_excludes_sources_with_no_items_in_window(self, auth_client, db_session):
        user = auth_client.current_user
        _make_source(db_session, user.id, name="Empty")
        db_session.commit()

        resp = _get(auth_client)
        assert resp.json() == []

    def test_does_not_count_another_users_items(self, auth_client, db_session, make_user):
        other = make_user(username="other")
        other_source = _make_source(db_session, other.id, name="OtherSource")
        _make_item(db_session, other_source, other.id, is_relevant=True)
        db_session.commit()

        resp = _get(auth_client)
        assert resp.json() == []
