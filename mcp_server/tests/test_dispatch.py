"""Tool dispatch: routing by resource type, idempotency, and guards."""

import httpx
import pytest


class TestActionRouting:
    def test_article_actions_hit_the_news_route(self, server):
        calls = []
        server._get = lambda p, params=None: {"is_read": False}
        server._patch = lambda p, body=None: calls.append(p)
        server._handle("mark_read", {"id": "i1"})
        assert calls == ["/news/i1/read"]

    def test_cluster_actions_hit_the_clusters_route(self, server):
        calls = []
        server._get = lambda p, params=None: {"is_read": False}
        server._patch = lambda p, body=None: calls.append(p)
        server._handle("mark_read", {"id": "cluster:c1"})
        assert calls == ["/clusters/c1/read"]

    def test_bookmark_routes_clusters_too(self, server):
        calls = []
        server._get = lambda p, params=None: {"read_later": False}
        server._patch = lambda p, body=None: calls.append(p)
        server._handle("bookmark", {"id": "cluster:c1"})
        assert calls == ["/clusters/c1/read-later"]


class TestIdempotency:
    """The underlying endpoints are toggles, so acting without checking
    current state turns a repeated call into its own undo."""

    def test_mark_read_skips_an_already_read_item(self, server):
        calls = []
        server._get = lambda p, params=None: {"is_read": True}
        server._patch = lambda p, body=None: calls.append(p)
        server._handle("mark_read", {"id": "i1"})
        assert calls == []

    def test_like_skips_an_already_liked_item(self, server):
        calls = []
        server._get = lambda p, params=None: {"is_relevant": True}
        server._patch = lambda p, body=None: calls.append(p)
        server._handle("like", {"id": "i1"})
        assert calls == []

    def test_like_acts_when_not_yet_liked(self, server):
        calls = []
        server._get = lambda p, params=None: {"is_relevant": False}
        server._patch = lambda p, body=None: calls.append(p)
        server._handle("like", {"id": "i1"})
        assert calls == ["/news/i1/relevant"]

    def test_dislike_needs_no_pre_read_because_it_is_not_a_toggle(self, server):
        calls = []
        server._patch = lambda p, body=None: calls.append(p)
        server._handle("dislike", {"id": "i1"})  # _get is unstubbed: must not be called
        assert calls == ["/news/i1/dislike"]


class TestGuards:
    def test_rejects_an_out_of_range_category_weight(self, server):
        assert "between 0.0 and 5.0" in server._handle(
            "set_category_weight", {"category_id": "c1", "manual_weight": 99})

    def test_rejects_an_empty_update(self, server):
        assert "Nothing to update" in server._handle("update_source", {"id": "s1"})

    def test_rejects_an_empty_topic_list(self, server):
        assert "at least one topic" in server._handle("keyword_trend", {"topics": []})

    def test_unknown_tool_is_reported_not_raised(self, server):
        assert server._handle("nope", {}) == "Unknown tool: nope"

    def test_public_feed_is_not_enabled_without_explicit_consent(self, server):
        # The resulting URL is unauthenticated, so enabling it is a decision
        # the user has to make, not a side effect of asking for the link.
        server._get = lambda p, params=None: {"public_feed_enabled": False}
        out = server._handle("get_podcast_feed_url", {"show_id": "s1"})
        assert "enable=true" in out and "unauthenticated" in out


class TestErrorSurface:
    def test_api_errors_become_readable_text(self, server):
        def boom(path, params=None):
            raise httpx.HTTPStatusError(
                "x", request=httpx.Request("GET", "http://t"),
                response=httpx.Response(404, text="nope"))
        server._get = boom
        assert server._call("get_learning_profile") == "API error 404: nope"

    def test_unset_optional_arguments_are_dropped_before_dispatch(self, server):
        # Several handlers distinguish absent from explicitly-set.
        seen = {}
        server._handle = lambda name, args: seen.update(args) or "ok"
        server._call("update_source", id="s1", name=None, is_active=False)
        assert seen == {"id": "s1", "is_active": False}
