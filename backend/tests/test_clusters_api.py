"""GET /clusters/{id}.

The action routes on this router are all toggles, so a client wanting
idempotent "mark read" semantics has to read current state first. Items have
always had GET /news/{id} for that; clusters had no single-resource fetch at
all, which is what made the MCP server unable to act on clustered stories
correctly (see mcp_server/server.py).
"""

import uuid

import pytest

from app.models import NewsCluster, NewsItem, Source


@pytest.fixture
def cluster_with_items(db_session, auth_client):
    user = auth_client.current_user
    src = Source(id=uuid.uuid4(), user_id=user.id, name="Feed A", source_type="rss",
                 config={"url": "https://a.example/feed"}, is_active=True)
    db_session.add(src)
    cluster = NewsCluster(
        id=uuid.uuid4(), user_id=user.id, title="Big story",
        unified_abstract="Three outlets covered this.",
        extracted_keywords=["policy", "ai"], relevance_score=9, impact_score=8,
        llm_processed=True,
    )
    db_session.add(cluster)
    db_session.flush()
    for n in (1, 2):
        db_session.add(NewsItem(
            id=uuid.uuid4(), user_id=user.id, source_id=src.id, cluster_id=cluster.id,
            title=f"Take {n}", url=f"https://a.example/{n}", url_hash=uuid.uuid4().hex,
        ))
    db_session.flush()
    return cluster


def test_returns_the_cluster_with_its_member_items(auth_client, cluster_with_items):
    resp = auth_client.get(f"/api/clusters/{cluster_with_items.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "cluster"  # the discriminator MCP routes on
    assert body["title"] == "Big story"
    assert body["unified_abstract"] == "Three outlets covered this."
    assert sorted(i["title"] for i in body["items"]) == ["Take 1", "Take 2"]


def test_exposes_the_flags_a_toggle_client_needs_to_pre_check(auth_client, cluster_with_items):
    body = auth_client.get(f"/api/clusters/{cluster_with_items.id}").json()
    assert body["is_read"] is False
    assert body["is_relevant"] is False
    assert body["read_later"] is False


def test_reflects_a_toggle_so_a_second_call_can_be_skipped(auth_client, cluster_with_items):
    auth_client.patch(f"/api/clusters/{cluster_with_items.id}/read")
    assert auth_client.get(f"/api/clusters/{cluster_with_items.id}").json()["is_read"] is True


def test_404s_for_another_users_cluster(auth_client, db_session, make_user):
    other = make_user(username="bob")
    foreign = NewsCluster(id=uuid.uuid4(), user_id=other.id, llm_processed=True)
    db_session.add(foreign)
    db_session.flush()

    assert auth_client.get(f"/api/clusters/{foreign.id}").status_code == 404


def test_404s_for_an_unknown_id(auth_client):
    assert auth_client.get(f"/api/clusters/{uuid.uuid4()}").status_code == 404


def test_requires_auth(auth_client, cluster_with_items):
    # auth_client IS client with a cookie set, so asking for both fixtures
    # would hand back the same already-authenticated client. Drop the cookie
    # instead of trying to get an anonymous one alongside the fixture that
    # needs a user to own the cluster.
    auth_client.cookies.clear()
    assert auth_client.get(f"/api/clusters/{cluster_with_items.id}").status_code == 401
