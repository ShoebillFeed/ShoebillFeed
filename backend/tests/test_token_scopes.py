"""API token capability scopes.

This is a security boundary, not a convenience: the MCP server is a client
holding one of these tokens, so anything it can't do via a hidden tool it
could still do by calling the REST API directly. Enforcement lives in
services/auth.py::get_current_user; these tests exercise it through real
requests rather than calling the matcher directly.
"""

import uuid

import pytest

from app.models.api_token import ApiToken
from app.services.auth import generate_api_token
from app.services.token_scopes import (
    ScopeDenied,
    check_request,
    normalize_scopes,
    required_scope,
)


@pytest.fixture
def make_token(db_session, make_user):
    def _make(scopes=None, user=None):
        user = user or make_user(username=f"u{uuid.uuid4().hex[:8]}")
        plaintext, token_hash = generate_api_token()
        db_session.add(ApiToken(user_id=user.id, name="t", token_hash=token_hash, scopes=scopes))
        db_session.flush()
        return plaintext
    return _make


def auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestRequiredScope:
    def test_maps_safe_and_unsafe_methods_differently(self):
        assert required_scope("GET", "/api/news") == "read"
        assert required_scope("PATCH", "/api/news/{item_id}/read") == "act"

    def test_write_to_sources_needs_curate_not_act(self):
        assert required_scope("GET", "/api/sources") == "read"
        assert required_scope("POST", "/api/sources") == "curate"

    def test_whole_routers_map_to_one_scope(self):
        assert required_scope("GET", "/api/learning/profile") == "learning"
        assert required_scope("PATCH", "/api/learning/categories/{id}/weight") == "learning"
        assert required_scope("GET", "/api/podcasts/episodes") == "podcasts"
        assert required_scope("POST", "/api/stats/keyword-trend") == "stats"

    def test_token_endpoints_are_barred_outright(self):
        # A token that can mint tokens can escalate past its own scopes and
        # outlive its revocation.
        for path in ("/api/tokens", "/api/tokens/{token_id}", "/api/auth/login"):
            with pytest.raises(ScopeDenied) as exc:
                required_scope("GET", path)
            assert exc.value.scope is None

    def test_self_introspection_is_ungated(self):
        assert required_scope("GET", "/api/settings/token-scopes") is None

    def test_unmapped_paths_are_ungated(self):
        assert required_scope("GET", "/api/something-new") is None


class TestNormalizeScopes:
    def test_none_stays_none_meaning_unrestricted(self):
        assert normalize_scopes(None) is None

    def test_drops_unknown_names_instead_of_rejecting(self):
        assert normalize_scopes(["read", "not-a-scope"]) == ["read"]

    def test_deduplicates_and_orders_canonically(self):
        assert normalize_scopes(["stats", "read", "read"]) == ["read", "stats"]

    def test_empty_list_stays_empty(self):
        assert normalize_scopes([]) == []


class TestCheckRequest:
    def test_unrestricted_token_passes_gated_paths(self):
        check_request(None, "POST", "/api/sources")

    def test_unrestricted_token_still_cannot_reach_tokens(self):
        with pytest.raises(ScopeDenied):
            check_request(None, "GET", "/api/tokens")

    def test_missing_scope_is_denied(self):
        with pytest.raises(ScopeDenied) as exc:
            check_request(["read"], "POST", "/api/sources")
        assert exc.value.scope == "curate"


class TestEnforcementOverHttp:
    def test_scoped_token_can_use_a_granted_route(self, client, make_token):
        token = make_token(["read"])
        assert client.get("/api/news", headers=auth(token)).status_code == 200

    def test_scoped_token_is_403ed_on_an_ungranted_route(self, client, make_token):
        token = make_token(["read"])
        resp = client.post("/api/sources", headers=auth(token),
                           json={"name": "x", "source_type": "rss", "config": {"url": "u"}})
        assert resp.status_code == 403
        assert "curate" in resp.json()["detail"]

    def test_read_scope_does_not_grant_acting(self, client, make_token):
        token = make_token(["read"])
        resp = client.patch(f"/api/news/{uuid.uuid4()}/read", headers=auth(token))
        # 403 for the scope, never 404 -- the scope check must run before the
        # route can leak whether that id exists.
        assert resp.status_code == 403

    def test_unrestricted_token_is_unaffected(self, client, make_token):
        # Every token predating this feature has scopes = NULL.
        token = make_token(None)
        assert client.get("/api/news", headers=auth(token)).status_code == 200

    def test_no_token_can_manage_tokens(self, client, make_token):
        for scopes in (None, ["read", "curate"]):
            resp = client.get("/api/tokens", headers=auth(make_token(scopes)))
            assert resp.status_code == 403
            assert "cannot access" in resp.json()["detail"]

    def test_cookie_sessions_are_never_scope_limited(self, auth_client):
        # Scopes limit a token, not a user in their own browser.
        assert auth_client.get("/api/tokens").status_code == 200

    def test_token_can_always_introspect_its_own_scopes(self, client, make_token):
        token = make_token(["read"])
        resp = client.get("/api/settings/token-scopes", headers=auth(token))
        assert resp.status_code == 200
        assert resp.json()["scopes"] == ["read"]
        assert any(s["key"] == "curate" for s in resp.json()["all_scopes"])

    def test_introspection_reports_null_for_an_unrestricted_token(self, client, make_token):
        resp = client.get("/api/settings/token-scopes", headers=auth(make_token(None)))
        assert resp.json()["scopes"] is None


class TestTokenCreation:
    def test_stores_normalized_scopes(self, auth_client):
        resp = auth_client.post("/api/tokens", json={"name": "mcp", "scopes": ["stats", "read", "bogus"]})
        assert resp.status_code == 201
        assert resp.json()["scopes"] == ["read", "stats"]

    def test_omitting_scopes_creates_an_unrestricted_token(self, auth_client):
        resp = auth_client.post("/api/tokens", json={"name": "full"})
        assert resp.json()["scopes"] is None

    def test_listing_reports_scopes(self, auth_client):
        auth_client.post("/api/tokens", json={"name": "ro", "scopes": ["read"]})
        assert any(t["scopes"] == ["read"] for t in auth_client.get("/api/tokens").json())

    def test_scope_catalog_is_available_to_the_settings_ui(self, auth_client):
        keys = [s["key"] for s in auth_client.get("/api/tokens/scopes").json()]
        assert "read" in keys and "podcasts" in keys
