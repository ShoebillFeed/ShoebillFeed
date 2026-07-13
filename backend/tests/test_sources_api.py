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
