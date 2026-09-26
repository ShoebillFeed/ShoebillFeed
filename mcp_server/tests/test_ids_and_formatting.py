"""Feed entries come in two shapes that live under different API prefixes.

Standalone articles are at /news/{id}, multi-source stories at
/clusters/{id}. They used to render identically, so the model would read a
cluster's bare UUID out of the feed and every action tool would aim it at
/news/{id} -- a 404, i.e. a like or bookmark that silently did nothing.
"""


class TestResolveId:
    def test_cluster_prefix_selects_the_clusters_route(self, server):
        assert server._resolve_id("cluster:abc") == ("/clusters", "abc")

    def test_bare_uuid_stays_an_article(self, server):
        # Search results are always articles and carry no prefix.
        assert server._resolve_id("abc") == ("/news", "abc")

    def test_surrounding_whitespace_is_tolerated(self, server):
        assert server._resolve_id("  cluster:abc  ") == ("/clusters", "abc")

    def test_round_trips_with_exposed_id(self, server):
        cluster = {"kind": "cluster", "id": "c1"}
        article = {"kind": "item", "id": "i1"}
        assert server._resolve_id(server._exposed_id(cluster)) == ("/clusters", "c1")
        assert server._resolve_id(server._exposed_id(article)) == ("/news", "i1")


class TestFormatting:
    def _cluster(self):
        return {
            "kind": "cluster", "id": "c1", "title": "Big story",
            "unified_abstract": "Three outlets covered this.",
            "items": [
                {"title": "Take A", "url": "https://a.test/1", "source": {"name": "A"}},
                {"title": "Take B", "url": "https://b.test/2", "source": {"name": "B"}},
            ],
        }

    def test_cluster_id_is_prefixed_so_actions_route_correctly(self, server):
        assert "ID: cluster:c1" in server._fmt_item(self._cluster())

    def test_article_id_is_left_bare(self, server):
        out = server._fmt_item({"kind": "item", "id": "i1", "title": "Solo"})
        assert "ID: i1" in out and "cluster:" not in out

    def test_cluster_summary_comes_from_unified_abstract(self, server):
        # Clusters have no `abstract`; reading only that showed no summary.
        assert "Three outlets covered this." in server._fmt_item(self._cluster())

    def test_cluster_names_its_member_sources(self, server):
        # Clusters have no top-level `source`, and the outlets are the whole
        # point of a cluster.
        out = server._fmt_item(self._cluster())
        assert "2 sources" in out and "A, B" in out

    def test_cluster_lists_member_headlines(self, server):
        out = server._fmt_item(self._cluster())
        assert "Take A" in out and "Take B" in out

    def test_article_still_shows_its_own_source_and_abstract(self, server):
        out = server._fmt_item({
            "kind": "item", "id": "i1", "title": "Solo", "abstract": "A summary.",
            "source": {"name": "Feed A"}, "relevance_score": 7,
        })
        assert "A summary." in out and "Feed A" in out and "Relevance: 7/10" in out
