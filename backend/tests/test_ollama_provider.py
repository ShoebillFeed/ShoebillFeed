from unittest.mock import patch

from app.services.llm.ollama_provider import OllamaProvider, _num_ctx_for


class TestNumCtxFor:
    def test_floor_for_short_prompts(self):
        assert _num_ctx_for("short system", "short user", 512) == 4096

    def test_scales_with_prompt_size(self):
        long_system = "word " * 5000  # ~25000 chars
        assert _num_ctx_for(long_system, "user", 4096) > 4096

    def test_uses_a_conservative_char_to_token_ratio(self):
        text = "x" * 3000
        assert _num_ctx_for(text, "", 0) == max(4096, 3000 // 3 + 512)

    def test_scales_with_requested_output_tokens(self):
        assert _num_ctx_for("s", "u", 20000) > _num_ctx_for("s", "u", 512)


class TestOllamaProviderIncludesNumCtx:
    """Regression coverage for the bug where num_predict was set but num_ctx
    wasn't -- a prompt + requested output larger than the model's default
    context window silently produced a truncated or empty response instead
    of erroring (surfaced by the podcast script prompt at longer episode
    lengths). Every payload-building method must set num_ctx explicitly."""

    def _provider(self):
        return OllamaProvider(base_url="http://ollama.test", model="qwen2.5:3b")

    def test_complete(self):
        provider = self._provider()
        with patch.object(provider, "_post", return_value={"response": "{}"}) as mock_post:
            provider._complete(system="sys", user="usr", max_tokens=2048)
        payload = mock_post.call_args.args[0]
        assert payload["options"]["num_ctx"] >= 4096

    def test_process_item(self):
        provider = self._provider()
        with patch.object(provider, "_post", return_value={"response": '{"keywords": [], "abstract": "x"}'}) as mock_post:
            provider.process_item("Title", "Content", categories=[])
        payload = mock_post.call_args.args[0]
        assert "num_ctx" in payload["options"]

    def test_process_cluster(self):
        provider = self._provider()
        response = '{"unified_abstract": "x", "keywords": [], "source_summaries": {}}'
        with patch.object(provider, "_post", return_value={"response": response}) as mock_post:
            provider.process_cluster(items=[{"title": "T", "content": "C", "source_name": "S"}], categories=[])
        payload = mock_post.call_args.args[0]
        assert "num_ctx" in payload["options"]

    def test_extract_newsletter_items(self):
        provider = self._provider()
        with patch.object(provider, "_post", return_value={"response": '{"items": []}'}) as mock_post:
            provider.extract_newsletter_items(content="hello", categories=[])
        payload = mock_post.call_args.args[0]
        assert "num_ctx" in payload["options"]

    def test_larger_prompt_gets_a_larger_num_ctx_than_a_small_one(self):
        provider = self._provider()
        with patch.object(provider, "_post", return_value={"response": '{"items": []}'}) as mock_post:
            provider.extract_newsletter_items(content="hi", categories=[])
        small_ctx = mock_post.call_args.args[0]["options"]["num_ctx"]

        with patch.object(provider, "_post", return_value={"response": '{"items": []}'}) as mock_post:
            provider.extract_newsletter_items(content="word " * 3000, categories=[])
        large_ctx = mock_post.call_args.args[0]["options"]["num_ctx"]

        assert large_ctx > small_ctx
