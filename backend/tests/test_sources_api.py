def test_create_and_list_source(auth_client):
    resp = auth_client.post(
        "/api/sources",
        json={"name": "Hacker News", "source_type": "rss", "config": {"url": "https://news.ycombinator.com/rss"}},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Hacker News"
    assert body["source_type"] == "rss"
    assert body["item_count"] == 0

    listed = auth_client.get("/api/sources")
    assert listed.status_code == 200
    names = [s["name"] for s in listed.json()]
    assert "Hacker News" in names


def test_create_source_requires_authentication(client):
    resp = client.post(
        "/api/sources",
        json={"name": "Hacker News", "source_type": "rss", "config": {"url": "https://news.ycombinator.com/rss"}},
    )
    assert resp.status_code == 401


def test_create_source_rejects_unknown_source_type(auth_client):
    resp = auth_client.post(
        "/api/sources",
        json={"name": "Bad", "source_type": "carrier-pigeon", "config": {}},
    )
    assert resp.status_code == 422


def test_update_source(auth_client):
    created = auth_client.post(
        "/api/sources",
        json={"name": "Old Name", "source_type": "rss", "config": {"url": "https://example.com/feed"}},
    ).json()

    resp = auth_client.patch(f"/api/sources/{created['id']}", json={"name": "New Name"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_source(auth_client):
    created = auth_client.post(
        "/api/sources",
        json={"name": "Temp", "source_type": "rss", "config": {"url": "https://example.com/feed"}},
    ).json()

    resp = auth_client.delete(f"/api/sources/{created['id']}")
    assert resp.status_code == 204

    listed = auth_client.get("/api/sources").json()
    assert created["id"] not in [s["id"] for s in listed]


def test_users_only_see_their_own_sources(client, make_user):
    from app.services.auth import create_token

    user1 = make_user(username="user1")
    user2 = make_user(username="user2")

    client.cookies.set("access_token", create_token(user1.id, user1.username))
    client.post("/api/sources", json={"name": "User1 Feed", "source_type": "rss", "config": {"url": "https://a.example/feed"}})

    client.cookies.set("access_token", create_token(user2.id, user2.username))
    listed = client.get("/api/sources").json()

    assert "User1 Feed" not in [s["name"] for s in listed]


class TestSourceStaleFlag:
    def _make_source(self, db_session, user_id, *, name="Feed", is_active=True, created_at):
        from app.models.source import Source

        source = Source(
            user_id=user_id, name=name, source_type="rss",
            config={"url": f"https://example.com/{name}"}, is_active=is_active,
        )
        db_session.add(source)
        db_session.flush()
        source.created_at = created_at
        db_session.flush()
        return source

    def _make_item(self, db_session, source, user_id, *, fetched_at):
        import uuid
        from app.models.news_item import NewsItem

        unique = uuid.uuid4().hex
        item = NewsItem(
            source_id=source.id, user_id=user_id, title=f"Article {unique}",
            url=f"https://example.com/{unique}", url_hash=f"hash-{unique}", fetched_at=fetched_at,
        )
        db_session.add(item)
        db_session.flush()
        return item

    def test_flags_an_old_active_source_with_no_recent_items(self, auth_client, db_session):
        from datetime import datetime, timedelta, timezone

        user = auth_client.current_user
        now = datetime.now(timezone.utc)
        source = self._make_source(db_session, user.id, created_at=now - timedelta(days=10))
        db_session.commit()

        resp = auth_client.get(f"/api/sources/{source.id}")
        assert resp.status_code == 200
        assert resp.json()["is_stale"] is True

    def test_does_not_flag_a_source_less_than_a_week_old(self, auth_client, db_session):
        from datetime import datetime, timedelta, timezone

        user = auth_client.current_user
        now = datetime.now(timezone.utc)
        source = self._make_source(db_session, user.id, created_at=now - timedelta(days=2))
        db_session.commit()

        resp = auth_client.get(f"/api/sources/{source.id}")
        assert resp.json()["is_stale"] is False

    def test_does_not_flag_an_inactive_source(self, auth_client, db_session):
        from datetime import datetime, timedelta, timezone

        user = auth_client.current_user
        now = datetime.now(timezone.utc)
        source = self._make_source(db_session, user.id, is_active=False, created_at=now - timedelta(days=10))
        db_session.commit()

        resp = auth_client.get(f"/api/sources/{source.id}")
        assert resp.json()["is_stale"] is False

    def test_does_not_flag_a_source_with_a_recent_item(self, auth_client, db_session):
        from datetime import datetime, timedelta, timezone

        user = auth_client.current_user
        now = datetime.now(timezone.utc)
        source = self._make_source(db_session, user.id, created_at=now - timedelta(days=10))
        self._make_item(db_session, source, user.id, fetched_at=now - timedelta(days=1))
        db_session.commit()

        resp = auth_client.get(f"/api/sources/{source.id}")
        assert resp.json()["is_stale"] is False

    def test_still_flags_a_source_whose_only_items_are_older_than_a_week(self, auth_client, db_session):
        from datetime import datetime, timedelta, timezone

        user = auth_client.current_user
        now = datetime.now(timezone.utc)
        source = self._make_source(db_session, user.id, created_at=now - timedelta(days=30))
        self._make_item(db_session, source, user.id, fetched_at=now - timedelta(days=20))
        db_session.commit()

        resp = auth_client.get(f"/api/sources/{source.id}")
        assert resp.json()["is_stale"] is True

    def test_list_endpoint_matches_single_get(self, auth_client, db_session):
        from datetime import datetime, timedelta, timezone

        user = auth_client.current_user
        now = datetime.now(timezone.utc)
        source = self._make_source(db_session, user.id, created_at=now - timedelta(days=10))
        db_session.commit()

        listed = auth_client.get("/api/sources").json()
        entry = next(s for s in listed if s["id"] == str(source.id))
        assert entry["is_stale"] is True
