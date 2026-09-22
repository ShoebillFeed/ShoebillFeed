from unittest.mock import MagicMock, patch

import pytest

from app.services import embedding
from app.services.embedding import EMBEDDING_DIM, generate_embedding


@pytest.fixture(autouse=True)
def ollama_configured(monkeypatch):
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "ollama_base_url", "http://ollama.test")
    monkeypatch.setattr(settings, "ollama_embedding_model", "nomic-embed-text")


def _resp(status=200, payload=None):
    r = MagicMock(status_code=status)
    r.json.return_value = payload or {}
    r.raise_for_status.return_value = None
    return r


class TestKeepAlive:
    """Without keep_alive, embeddings fall back to Ollama's 5-minute default
    and the embedding model unloads between processing batches, paying a full
    reload on the next one. The generate path already pins 30m."""

    def test_sent_on_the_modern_embed_endpoint(self):
        ok = _resp(payload={"embeddings": [[0.1] * EMBEDDING_DIM]})
        with patch.object(embedding.httpx, "post", return_value=ok) as post:
            generate_embedding("hello")
        assert post.call_args.kwargs["json"]["keep_alive"] == embedding._KEEP_ALIVE

    def test_sent_on_the_legacy_embeddings_fallback(self):
        legacy = _resp(payload={"embedding": [0.1] * EMBEDDING_DIM})
        with patch.object(embedding.httpx, "post", side_effect=[_resp(status=404), legacy]) as post:
            generate_embedding("hello")
        # Second call is the /api/embeddings retry.
        assert post.call_args.args[0].endswith("/api/embeddings")
        assert post.call_args.kwargs["json"]["keep_alive"] == embedding._KEEP_ALIVE


class TestGenerateEmbedding:
    def test_returns_the_vector_from_the_modern_endpoint(self):
        ok = _resp(payload={"embeddings": [[0.5] * EMBEDDING_DIM]})
        with patch.object(embedding.httpx, "post", return_value=ok):
            assert generate_embedding("hello") == [0.5] * EMBEDDING_DIM

    def test_returns_none_on_a_dimension_mismatch(self):
        # A wrong OLLAMA_EMBEDDING_MODEL must not write a bad-width vector
        # into a column declared vector(768).
        ok = _resp(payload={"embeddings": [[0.5] * 512]})
        with patch.object(embedding.httpx, "post", return_value=ok):
            assert generate_embedding("hello") is None

    def test_returns_none_when_ollama_is_unreachable(self):
        # Callers treat None as "fall back to keyword clustering".
        with patch.object(embedding.httpx, "post", side_effect=Exception("refused")):
            assert generate_embedding("hello") is None

    def test_returns_none_without_a_configured_base_url(self, monkeypatch):
        from app.config import get_settings

        monkeypatch.setattr(get_settings(), "ollama_base_url", "")
        with patch.object(embedding.httpx, "post") as post:
            assert generate_embedding("hello") is None
        post.assert_not_called()
