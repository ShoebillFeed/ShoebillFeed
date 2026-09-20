import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.llm import usage


_FROZEN_NOW = 1_700_000_000.0


@pytest.fixture
def frozen_clock():
    with patch.object(usage.time, "time", return_value=_FROZEN_NOW):
        yield usage._bucket(_FROZEN_NOW)


@pytest.fixture
def fake_redis():
    """Swaps the module's cached Redis client for a stub. The lru_cache is
    cleared either side so a real client is never constructed and no other
    test inherits the stub."""
    usage._client.cache_clear()
    client = MagicMock()
    with patch.object(usage, "_client", return_value=client):
        yield client
    usage._client.cache_clear()


class TestBucketing:
    def test_buckets_are_one_minute_wide(self):
        aligned = 1_000_000_020.0  # exactly on a minute boundary
        assert usage._bucket(aligned) == usage._bucket(aligned + 59)
        assert usage._bucket(aligned + 60) == usage._bucket(aligned) + 1

    def test_key_includes_model_and_bucket(self):
        assert usage._key("qwen3:8b", 42) == "shoebill:llm:req:qwen3:8b:42"


class TestRecordRequest:
    def test_increments_the_current_bucket_and_sets_a_ttl(self, fake_redis, frozen_clock):
        pipe = fake_redis.pipeline.return_value
        usage.record_request("qwen3:8b")
        assert pipe.incrby.call_args.args == (usage._key("qwen3:8b", frozen_clock), 1)
        assert pipe.expire.call_args.args[1] == usage._BUCKET_TTL_SECONDS
        pipe.execute.assert_called_once()

    def test_records_a_batch_as_many_requests(self, fake_redis):
        pipe = fake_redis.pipeline.return_value
        usage.record_request("claude-haiku-4-5", 50)
        assert pipe.incrby.call_args.args[1] == 50

    def test_ignores_an_empty_model_name(self, fake_redis):
        usage.record_request("")
        fake_redis.pipeline.assert_not_called()

    def test_ignores_a_non_positive_count(self, fake_redis):
        usage.record_request("qwen3:8b", 0)
        fake_redis.pipeline.assert_not_called()

    def test_never_raises_when_redis_is_down(self, fake_redis):
        # Telemetry must not be the reason an actual LLM call fails.
        fake_redis.pipeline.side_effect = ConnectionError("refused")
        usage.record_request("qwen3:8b")  # must not raise


class TestRequestCounts:
    def test_splits_rolling_hour_from_rolling_day(self, fake_redis):
        # Newest bucket first: 1 request/minute for the full day means 60 in
        # the last hour and 1440 over the day.
        fake_redis.mget.return_value = ["1"] * usage._DAY_MINUTES
        counts = usage.request_counts(["qwen3:8b"])
        assert counts["qwen3:8b"] == {"hour": 60, "day": 1440}

    def test_older_than_an_hour_counts_only_toward_the_day(self, fake_redis):
        raw = [None] * usage._DAY_MINUTES
        raw[usage._HOUR_MINUTES] = "7"  # one bucket past the hour boundary
        fake_redis.mget.return_value = raw
        counts = usage.request_counts(["qwen3:8b"])
        assert counts["qwen3:8b"] == {"hour": 0, "day": 7}

    def test_treats_missing_buckets_as_zero(self, fake_redis):
        fake_redis.mget.return_value = [None] * usage._DAY_MINUTES
        assert usage.request_counts(["qwen3:8b"])["qwen3:8b"] == {"hour": 0, "day": 0}

    def test_asks_for_a_full_day_of_buckets_newest_first(self, fake_redis, frozen_clock):
        fake_redis.mget.return_value = [None] * usage._DAY_MINUTES
        usage.request_counts(["qwen3:8b"])
        keys = fake_redis.mget.call_args.args[0]
        assert len(keys) == usage._DAY_MINUTES
        assert keys[0] == usage._key("qwen3:8b", frozen_clock)
        assert keys[-1] == usage._key("qwen3:8b", frozen_clock - usage._DAY_MINUTES + 1)

    def test_reports_zeros_rather_than_failing_when_redis_is_down(self, fake_redis):
        fake_redis.mget.side_effect = ConnectionError("refused")
        assert usage.request_counts(["qwen3:8b"]) == {"qwen3:8b": {"hour": 0, "day": 0}}

    def test_counts_each_model_separately(self, fake_redis):
        fake_redis.mget.side_effect = [
            ["2"] + [None] * (usage._DAY_MINUTES - 1),
            ["5"] + [None] * (usage._DAY_MINUTES - 1),
        ]
        counts = usage.request_counts(["qwen3:8b", "claude-haiku-4-5"])
        assert counts["qwen3:8b"]["day"] == 2
        assert counts["claude-haiku-4-5"]["day"] == 5

    def test_skips_empty_model_names(self, fake_redis):
        assert usage.request_counts([""]) == {}
        fake_redis.mget.assert_not_called()


class TestLLMUsageEndpoint:
    def test_reports_the_configured_model(self, client, monkeypatch):
        from app.config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "llm_providers", "ollama")
        monkeypatch.setattr(settings, "ollama_model", "qwen3:8b")

        with patch("app.services.llm.usage.request_counts", return_value={"qwen3:8b": {"hour": 3, "day": 9}}):
            resp = client.get("/api/settings/llm-usage")

        assert resp.status_code == 200
        assert resp.json()["models"] == [{"model": "qwen3:8b", "hour": 3, "day": 9}]

    def test_lists_a_shared_model_once(self, client, monkeypatch):
        # Both providers configured against the same model name must not
        # produce two identical rows in the panel.
        from app.config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "llm_providers", "ollama,anthropic")
        monkeypatch.setattr(settings, "ollama_model", "same-model")
        monkeypatch.setattr(settings, "anthropic_model", "same-model")

        captured = {}

        def fake_counts(models):
            captured["models"] = models
            return {m: {"hour": 0, "day": 0} for m in models}

        with patch("app.services.llm.usage.request_counts", fake_counts):
            resp = client.get("/api/settings/llm-usage")

        assert captured["models"] == ["same-model"]
        assert len(resp.json()["models"]) == 1
