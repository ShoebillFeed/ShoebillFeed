"""Tool filtering by the token's capability scopes.

Usability only: the security boundary is the API's own scope check in
backend/app/services/token_scopes.py, which applies whether or not a client
filters. What this must not do is hide the whole surface by accident.
"""

import asyncio


def _tool_names(mod):
    return sorted(t.name for t in asyncio.run(mod.mcp.list_tools()))


def _with_scopes(load_server, scopes, fail=False):
    mod = load_server()
    if fail:
        def boom(path, params=None):
            raise RuntimeError("unreachable")
        mod._get = boom
    else:
        mod._get = lambda path, params=None: {"scopes": scopes}
    mod._apply_scope_filter()
    return mod


class TestScopeMap:
    def test_every_registered_tool_has_a_scope(self, server):
        # An unmapped tool would survive every filter, silently escaping the
        # feature -- the API would still reject it, but the model would be
        # offered something it cannot use.
        registered = {t.name for t in asyncio.run(server.mcp.list_tools())}
        assert registered == set(server._TOOL_SCOPES)

    def test_scope_names_match_the_backend_catalog(self, server):
        # Kept in lockstep with backend/app/services/token_scopes.py.
        assert set(server._TOOL_SCOPES.values()) == {
            "read", "act", "curate", "learning", "podcasts", "stats"}


class TestFiltering:
    def test_unrestricted_token_keeps_every_tool(self, load_server):
        mod = _with_scopes(load_server, None)
        assert len(_tool_names(mod)) == len(mod._TOOL_SCOPES)

    def test_read_only_token_keeps_only_read_tools(self, load_server):
        mod = _with_scopes(load_server, ["read"])
        names = _tool_names(mod)
        assert "get_feed" in names
        assert "like" not in names
        assert "add_source" not in names
        assert all(mod._TOOL_SCOPES[n] == "read" for n in names)

    def test_scopes_combine(self, load_server):
        names = _tool_names(_with_scopes(load_server, ["read", "act"]))
        assert "get_feed" in names and "like" in names and "add_source" not in names

    def test_a_single_non_read_scope_works_alone(self, load_server):
        names = _tool_names(_with_scopes(load_server, ["podcasts"]))
        assert names == ["generate_podcast_episode", "get_podcast_feed_url",
                         "list_podcast_episodes", "list_podcast_shows"]

    def test_empty_scope_list_leaves_no_tools(self, load_server):
        assert _tool_names(_with_scopes(load_server, [])) == []

    def test_unreachable_introspection_fails_open(self, load_server):
        # An older server without the endpoint, or a network blip, must not
        # present an empty server that looks broken -- let the API decide.
        mod = _with_scopes(load_server, None, fail=True)
        assert len(_tool_names(mod)) == len(mod._TOOL_SCOPES)
