from app.services.deduplication import canonical_url, content_hash, url_hash


class TestCanonicalUrl:
    def test_strips_utm_params(self):
        assert canonical_url("https://example.com/a?utm_source=x&utm_medium=y") == "https://example.com/a"

    def test_strips_tracking_and_session_params(self):
        url = "https://example.com/a?fbclid=abc&jsessionid=123&ref=homepage"
        assert canonical_url(url) == "https://example.com/a"

    def test_keeps_real_query_params(self):
        assert canonical_url("https://example.com/a?id=42") == "https://example.com/a?id=42"

    def test_keeps_real_params_alongside_tracking_params(self):
        url = "https://example.com/a?id=42&utm_source=newsletter"
        assert canonical_url(url) == "https://example.com/a?id=42"

    def test_sorts_remaining_params_for_stable_ordering(self):
        a = canonical_url("https://example.com/a?z=1&a=2")
        b = canonical_url("https://example.com/a?a=2&z=1")
        assert a == b == "https://example.com/a?a=2&z=1"

    def test_drops_fragment(self):
        assert canonical_url("https://example.com/a#section-2") == "https://example.com/a"

    def test_tracking_param_match_is_case_insensitive(self):
        assert canonical_url("https://example.com/a?UTM_Source=x") == "https://example.com/a"


class TestUrlHash:
    def test_deterministic(self):
        url = "https://example.com/article"
        assert url_hash(url) == url_hash(url)

    def test_ignores_tracking_params(self):
        assert url_hash("https://example.com/a?utm_source=x") == url_hash("https://example.com/a?utm_source=y")

    def test_different_paths_hash_differently(self):
        assert url_hash("https://example.com/a") != url_hash("https://example.com/b")

    def test_is_hex_sha256(self):
        h = url_hash("https://example.com/a")
        assert len(h) == 64
        int(h, 16)  # raises ValueError if not valid hex


class TestContentHash:
    def test_deterministic(self):
        text = "Some article body text."
        assert content_hash(text) == content_hash(text)

    def test_only_considers_first_2000_chars(self):
        base = "x" * 2000
        assert content_hash(base + "tail-a") == content_hash(base + "tail-b")

    def test_different_content_hashes_differently(self):
        assert content_hash("Article A") != content_hash("Article B")
