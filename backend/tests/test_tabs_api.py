def test_create_tab_with_icon(auth_client):
    resp = auth_client.post("/api/tabs", json={"name": "Work", "icon": "briefcase"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Work"
    assert body["icon"] == "briefcase"


def test_create_tab_requires_icon(auth_client):
    resp = auth_client.post("/api/tabs", json={"name": "No Icon"})
    assert resp.status_code == 422


def test_create_tab_rejects_null_icon(auth_client):
    resp = auth_client.post("/api/tabs", json={"name": "No Icon", "icon": None})
    assert resp.status_code == 422


def test_create_tab_rejects_unknown_icon(auth_client):
    resp = auth_client.post("/api/tabs", json={"name": "Bad", "icon": "not-a-real-icon"})
    assert resp.status_code == 422


def test_create_tab_rejects_icon_already_used_elsewhere_in_app(auth_client):
    # Bookmark is the Read Later tab's icon -- not in the selectable set.
    resp = auth_client.post("/api/tabs", json={"name": "Bad", "icon": "bookmark"})
    assert resp.status_code == 422


def test_update_tab_icon(auth_client):
    created = auth_client.post("/api/tabs", json={"name": "Sports", "icon": "flag"}).json()
    resp = auth_client.patch(f"/api/tabs/{created['id']}", json={"icon": "trophy"})
    assert resp.status_code == 200
    assert resp.json()["icon"] == "trophy"


def test_update_tab_can_clear_icon(auth_client):
    # Not possible from the app's own UI (icon is required at creation and
    # the form always keeps one selected), but the API itself still permits
    # it since existing rows predating this feature can legitimately be
    # icon-less -- update shouldn't be stricter than that existing state.
    created = auth_client.post("/api/tabs", json={"name": "Sports", "icon": "trophy"}).json()
    resp = auth_client.patch(f"/api/tabs/{created['id']}", json={"icon": None})
    assert resp.status_code == 200
    assert resp.json()["icon"] is None
