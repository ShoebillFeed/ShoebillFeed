import uuid

from app.services.clustering import _jaccard, _matches, _title_words, cluster_new_items
from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem
from app.models.source import Source


class TestJaccard:
    def test_identical_sets(self):
        s = frozenset({"a", "b", "c"})
        assert _jaccard(s, s) == 1.0

    def test_disjoint_sets(self):
        assert _jaccard(frozenset({"a"}), frozenset({"b"})) == 0.0

    def test_partial_overlap(self):
        a = frozenset({"a", "b"})
        b = frozenset({"b", "c"})
        # intersection {b} = 1, union {a,b,c} = 3
        assert _jaccard(a, b) == 1 / 3

    def test_either_empty_is_zero(self):
        assert _jaccard(frozenset(), frozenset({"a"})) == 0.0
        assert _jaccard(frozenset({"a"}), frozenset()) == 0.0


class TestMatches:
    def test_requires_minimum_shared_count_even_if_ratio_is_high(self):
        # 1 shared word out of a small union can clear a similarity ratio
        # threshold, but should still be rejected by the absolute floor.
        a = frozenset({"apple"})
        b = frozenset({"apple"})
        assert not _matches(a, b, threshold=0.3, min_shared=2)

    def test_matches_when_both_thresholds_clear(self):
        a = frozenset({"apple", "vision", "pro"})
        b = frozenset({"apple", "vision", "launch"})
        # shared={apple,vision}=2, union has 4 -> ratio 0.5
        assert _matches(a, b, threshold=0.3, min_shared=2)

    def test_rejects_below_ratio_threshold(self):
        a = frozenset({"apple", "vision", "pro", "review", "hands", "on"})
        b = frozenset({"apple", "vision", "unrelated1", "unrelated2", "unrelated3", "unrelated4"})
        assert not _matches(a, b, threshold=0.5, min_shared=2)

    def test_either_empty_never_matches(self):
        assert not _matches(frozenset(), frozenset({"a", "b"}), threshold=0.0, min_shared=0)


class TestTitleWords:
    def test_excludes_stop_words(self):
        words = _title_words("The report on the economy")
        assert "the" not in words
        assert "on" not in words

    def test_excludes_short_tokens(self):
        words = _title_words("AI is big")
        assert "ai" not in words  # len 2, filtered regardless of case
        assert "is" not in words  # stop word

    def test_excludes_pure_digit_tokens(self):
        words = _title_words("Earnings 2024 report")
        assert "2024" not in words

    def test_keeps_content_words(self):
        words = _title_words("Bitcoin price surges past record threshold")
        # None of these are stop words, all length > 2 and non-numeric,
        # so they should survive filtering (possibly lemmatized).
        assert len(words) > 0
        assert "bitcoin" in words

    def test_is_case_insensitive(self):
        assert _title_words("Bitcoin Surges") == _title_words("bitcoin surges")


class TestClusterNewItems:
    def _make_source(self, db_session, user_id):
        source = Source(user_id=user_id, name="Test Feed", source_type="rss", config={"url": "https://example.com/feed"})
        db_session.add(source)
        db_session.flush()
        return source

    def _make_item(self, db_session, source, user_id, title, url):
        item = NewsItem(source_id=source.id, user_id=user_id, title=title, url=url, url_hash=url)
        db_session.add(item)
        db_session.flush()
        return item

    def test_similar_titles_get_clustered_together(self, db_session, make_user):
        user = make_user()
        source = self._make_source(db_session, user.id)
        a = self._make_item(db_session, source, user.id, "Central Bank Raises Interest Rates Sharply", "https://a.example/1")
        b = self._make_item(db_session, source, user.id, "Central Bank Sharply Raises Interest Rates Again", "https://b.example/1")
        db_session.flush()

        result = cluster_new_items(db_session, [a.id, b.id])
        db_session.commit()

        assert result[a.id] is not None
        assert result[a.id] == result[b.id]
        cluster = db_session.get(NewsCluster, result[a.id])
        assert cluster is not None
        assert cluster.user_id == user.id

    def test_dissimilar_titles_stay_standalone(self, db_session, make_user):
        user = make_user()
        source = self._make_source(db_session, user.id)
        a = self._make_item(db_session, source, user.id, "Central Bank Raises Interest Rates", "https://a.example/2")
        b = self._make_item(db_session, source, user.id, "Local Sports Team Wins Championship Game", "https://b.example/2")
        db_session.flush()

        result = cluster_new_items(db_session, [a.id, b.id])
        db_session.commit()

        assert result[a.id] is None
        assert result[b.id] is None

    def test_clustering_never_crosses_user_boundaries(self, db_session, make_user):
        user1 = make_user(username="user1")
        user2 = make_user(username="user2")
        source1 = self._make_source(db_session, user1.id)
        source2 = self._make_source(db_session, user2.id)
        # Two near-identical titles within user1 -> would normally form a cluster.
        a1 = self._make_item(db_session, source1, user1.id, "Central Bank Raises Interest Rates Sharply", "https://a.example/3")
        a2 = self._make_item(db_session, source1, user1.id, "Central Bank Sharply Raises Interest Rates Again", "https://a.example/4")
        # user2's item has the same title, but must never be pulled into user1's cluster.
        b1 = self._make_item(db_session, source2, user2.id, "Central Bank Raises Interest Rates Sharply", "https://b.example/3")
        db_session.flush()

        result = cluster_new_items(db_session, [a1.id, a2.id, b1.id])
        db_session.commit()

        assert result[a1.id] is not None
        assert result[a1.id] == result[a2.id]
        # b1 is alone within its own user's batch, so it can't form a cluster
        # (needs >= 2 members) -- and critically, it must not equal user1's cluster.
        assert result[b1.id] != result[a1.id]
