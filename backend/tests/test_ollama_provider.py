from unittest.mock import patch

import httpx

from app.services.llm.ollama_provider import OllamaProvider, _num_ctx_for, _timeout_for


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


class TestOllamaProviderThinkFallback:
    """Regression coverage: once a `think: true` request 400s (some models,
    e.g. gemma3, don't support the think/no-think toggle at all -- confirmed
    against a real deployment's logs), every subsequent call must skip
    sending `think` altogether instead of paying a wasted extra round-trip
    on *every single future request* too, not just the first."""

    def _provider(self):
        return OllamaProvider(base_url="http://ollama.test", model="gemma3:12b")

    def _response(self, status_code, body=None):
        return httpx.Response(
            status_code,
            json=body if body is not None else {"response": "{}"},
            request=httpx.Request("POST", "http://ollama.test/api/generate"),
        )

    def test_falls_back_and_retries_once_on_a_think_unsupported_400(self):
        provider = self._provider()
        with patch.object(provider.client, "post", side_effect=[self._response(400), self._response(200)]) as mock_post:
            result = provider._post({"model": "gemma3:12b", "think": True})
        assert result == {"response": "{}"}
        assert mock_post.call_count == 2
        assert mock_post.call_args_list[1].kwargs["json"]["think"] is False

    def test_caches_think_unsupported_so_later_calls_skip_the_wasted_request(self):
        provider = self._provider()
        with patch.object(provider.client, "post", side_effect=[self._response(400), self._response(200)]):
            provider._post({"model": "gemma3:12b", "think": True})
        assert provider._think_unsupported is True

        with patch.object(provider.client, "post", return_value=self._response(200)) as mock_post:
            provider._post({"model": "gemma3:12b", "think": True})
        # Only one request this time -- no wasted 400 round-trip.
        assert mock_post.call_count == 1
        assert mock_post.call_args.kwargs["json"]["think"] is False

    def test_does_not_touch_think_when_the_model_supports_it(self):
        provider = self._provider()
        with patch.object(provider.client, "post", return_value=self._response(200)) as mock_post:
            provider._post({"model": "qwen3:8b", "think": True})
        assert mock_post.call_count == 1
        assert mock_post.call_args.kwargs["json"]["think"] is True
        assert provider._think_unsupported is False

    def test_a_400_unrelated_to_think_is_not_retried(self):
        provider = self._provider()
        with patch.object(provider.client, "post", return_value=self._response(400)) as mock_post:
            try:
                provider._post({"model": "gemma3:12b"})  # no "think" key at all
                raised = False
            except httpx.HTTPStatusError:
                raised = True
        assert raised
        assert mock_post.call_count == 1


class TestTimeoutFor:
    def test_floor_for_small_outputs(self):
        assert _timeout_for(max_tokens=256, floor=300.0) == 300.0

    def test_scales_above_the_floor_for_large_outputs(self):
        # A max-length podcast episode's script call (8192 tokens) at the
        # conservative slow-CPU estimate should run well past a 300s floor.
        assert _timeout_for(max_tokens=8192, floor=300.0) > 300.0

    def test_respects_a_higher_configured_floor(self):
        assert _timeout_for(max_tokens=100, floor=900.0) == 900.0


class TestOllamaProviderIncludesTimeout:
    """Regression coverage for the bug this fixes: a large generation (e.g.
    the podcast script, once num_ctx started letting it actually run to
    completion instead of returning a fast truncated response) could exceed
    the client's fixed request timeout and fail as a timeout error instead
    of succeeding slowly. The per-request timeout must scale with the
    requested output size, not stay fixed at the configured floor."""

    def _provider(self, timeout=300):
        return OllamaProvider(base_url="http://ollama.test", model="qwen2.5:3b", timeout=timeout)

    def test_complete_uses_a_timeout_scaled_to_max_tokens(self):
        provider = self._provider(timeout=300)
        with patch.object(provider, "_post", return_value={"response": "{}"}) as mock_post:
            provider._complete(system="sys", user="usr", max_tokens=8192)
        assert mock_post.call_args.kwargs["timeout"] > 300

    def test_complete_falls_back_to_the_configured_floor_for_small_calls(self):
        provider = self._provider(timeout=300)
        with patch.object(provider, "_post", return_value={"response": "{}"}) as mock_post:
            provider._complete(system="sys", user="usr", max_tokens=256)
        assert mock_post.call_args.kwargs["timeout"] == 300

    def test_process_item_passes_a_timeout(self):
        provider = self._provider()
        with patch.object(provider, "_post", return_value={"response": '{"keywords": [], "abstract": "x"}'}) as mock_post:
            provider.process_item("Title", "Content", categories=[])
        assert mock_post.call_args.kwargs["timeout"] is not None

    def test_process_cluster_passes_a_timeout(self):
        provider = self._provider()
        response = '{"unified_abstract": "x", "keywords": [], "source_summaries": {}}'
        with patch.object(provider, "_post", return_value={"response": response}) as mock_post:
            provider.process_cluster(items=[{"title": "T", "content": "C", "source_name": "S"}], categories=[])
        assert mock_post.call_args.kwargs["timeout"] is not None

    def test_extract_newsletter_items_passes_a_timeout(self):
        provider = self._provider()
        with patch.object(provider, "_post", return_value={"response": '{"items": []}'}) as mock_post:
            provider.extract_newsletter_items(content="hello", categories=[])
        assert mock_post.call_args.kwargs["timeout"] is not None
