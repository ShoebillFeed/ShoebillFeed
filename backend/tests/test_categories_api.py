def test_create_and_list_category(auth_client):
    resp = auth_client.post("/api/categories", json={"name": "Technology", "keywords": ["ai", "software"]})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Technology"
    assert body["keywords"] == ["ai", "software"]
    assert body["is_active"] is True

    listed = auth_client.get("/api/categories")
    assert listed.status_code == 200
    names = [c["name"] for c in listed.json()]
    assert "Technology" in names


def test_create_category_requires_authentication(client):
    resp = client.post("/api/categories", json={"name": "Technology"})
    assert resp.status_code == 401


def test_create_category_rejects_invalid_color(auth_client):
    resp = auth_client.post("/api/categories", json={"name": "Technology", "color": "not-a-color"})
    assert resp.status_code == 422


def test_update_category(auth_client):
    created = auth_client.post("/api/categories", json={"name": "Old Name"}).json()

    resp = auth_client.patch(f"/api/categories/{created['id']}", json={"name": "New Name", "is_active": False})

    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["is_active"] is False


def test_delete_category(auth_client):
    created = auth_client.post("/api/categories", json={"name": "Temp"}).json()

    resp = auth_client.delete(f"/api/categories/{created['id']}")
    assert resp.status_code == 204

    listed = auth_client.get("/api/categories").json()
    assert created["id"] not in [c["id"] for c in listed]
