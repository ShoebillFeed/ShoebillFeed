import os
from unittest.mock import MagicMock, patch

import pytest

from app.services.tts.network_provider import NetworkTTSProvider, _timeout_for


def _provider():
    return NetworkTTSProvider(base_url="http://tts.test:8100")


class TestListVoices:
    def test_parses_voice_list_from_the_service_response(self):
        provider = _provider()
        fake_resp = MagicMock()
        fake_resp.json.return_value = [
            {"id": "en_US-libritts_r-medium#0", "language": "en", "label": "Speaker 0"},
        ]
        with patch.object(provider.client, "get", return_value=fake_resp) as mock_get:
            voices = provider.list_voices("en")

        assert mock_get.call_args.kwargs["params"] == {"language": "en"}
        assert voices[0].id == "en_US-libritts_r-medium#0"
        assert voices[0].language == "en"
        assert voices[0].label == "Speaker 0"

    def test_raises_on_a_non_2xx_response(self):
        import httpx

        provider = _provider()
        fake_resp = MagicMock()
        fake_resp.raise_for_status.side_effect = httpx.HTTPStatusError("boom", request=MagicMock(), response=MagicMock())
        with patch.object(provider.client, "get", return_value=fake_resp):
            with pytest.raises(httpx.HTTPStatusError):
                provider.list_voices("en")


class TestTimeoutFor:
    def test_floors_at_the_configured_default_for_short_text(self):
        assert _timeout_for("hi", floor=120.0) == 120.0

    def test_scales_up_for_long_text(self):
        assert _timeout_for("x" * 1000, floor=120.0) > 120.0

    def test_never_goes_below_a_custom_floor(self):
        assert _timeout_for("short", floor=900.0) == 900.0


class TestSynthesize:
    def test_writes_response_bytes_to_out_path_and_reads_duration_header(self, tmp_path):
        provider = _provider()
        fake_resp = MagicMock()
        fake_resp.content = b"RIFF....fake wav bytes"
        fake_resp.headers = {"X-Duration-Seconds": "4.2"}
        out_path = str(tmp_path / "turn.wav")

        with patch.object(provider.client, "post", return_value=fake_resp) as mock_post:
            result = provider.synthesize("Hello there", "en_US-libritts_r-medium#0", out_path, speech_rate=1.5)

        assert mock_post.call_args.kwargs["json"] == {
            "text": "Hello there", "voice_id": "en_US-libritts_r-medium#0", "speech_rate": 1.5, "exaggeration": None,
        }
        assert os.path.exists(out_path)
        with open(out_path, "rb") as f:
            assert f.read() == b"RIFF....fake wav bytes"
        assert result.audio_path == out_path
        assert result.duration_seconds == 4.2

    def test_passes_exaggeration_through_when_given(self, tmp_path):
        provider = _provider()
        fake_resp = MagicMock()
        fake_resp.content = b"bytes"
        fake_resp.headers = {"X-Duration-Seconds": "1.0"}
        out_path = str(tmp_path / "turn.wav")

        with patch.object(provider.client, "post", return_value=fake_resp) as mock_post:
            provider.synthesize("Hi", "voice", out_path, exaggeration=0.8)

        assert mock_post.call_args.kwargs["json"]["exaggeration"] == 0.8

    def test_creates_parent_directories(self, tmp_path):
        provider = _provider()
        fake_resp = MagicMock()
        fake_resp.content = b"bytes"
        fake_resp.headers = {"X-Duration-Seconds": "1.0"}
        out_path = str(tmp_path / "nested" / "dir" / "turn.wav")

        with patch.object(provider.client, "post", return_value=fake_resp):
            provider.synthesize("Hi", "voice", out_path)

        assert os.path.exists(out_path)

    def test_defaults_duration_to_zero_when_header_missing(self, tmp_path):
        provider = _provider()
        fake_resp = MagicMock()
        fake_resp.content = b"bytes"
        fake_resp.headers = {}
        out_path = str(tmp_path / "turn.wav")

        with patch.object(provider.client, "post", return_value=fake_resp):
            result = provider.synthesize("Hi", "voice", out_path)

        assert result.duration_seconds == 0.0

    def test_request_timeout_scales_with_text_length(self, tmp_path):
        # A long script turn on a slow (e.g. Chatterbox-class) engine must not
        # be capped at the provider's default timeout -- see _timeout_for().
        provider = NetworkTTSProvider(base_url="http://tts.test:8100", timeout=120.0)
        fake_resp = MagicMock()
        fake_resp.content = b"bytes"
        fake_resp.headers = {"X-Duration-Seconds": "1.0"}
        out_path = str(tmp_path / "turn.wav")
        long_text = "word " * 2000

        with patch.object(provider.client, "post", return_value=fake_resp) as mock_post:
            provider.synthesize(long_text, "voice", out_path)

        assert mock_post.call_args.kwargs["timeout"] > 120.0

    def test_request_timeout_floors_at_the_configured_default_for_short_text(self, tmp_path):
        provider = NetworkTTSProvider(base_url="http://tts.test:8100", timeout=120.0)
        fake_resp = MagicMock()
        fake_resp.content = b"bytes"
        fake_resp.headers = {"X-Duration-Seconds": "1.0"}
        out_path = str(tmp_path / "turn.wav")

        with patch.object(provider.client, "post", return_value=fake_resp) as mock_post:
            provider.synthesize("Hi", "voice", out_path)

        assert mock_post.call_args.kwargs["timeout"] == 120.0


class TestHealthCheck:
    def test_healthy_on_200(self):
        provider = _provider()
        fake_resp = MagicMock(status_code=200)
        fake_resp.json.return_value = {"status": "ok"}
        with patch.object(provider.client, "get", return_value=fake_resp) as mock_get:
            assert provider.health_check() is True
        assert mock_get.call_args.args[0] == "http://tts.test:8100/health"
        assert mock_get.call_args.kwargs["timeout"] == 5.0

    def test_unhealthy_on_non_200(self):
        provider = _provider()
        fake_resp = MagicMock(status_code=503)
        with patch.object(provider.client, "get", return_value=fake_resp):
            assert provider.health_check() is False

    def test_unhealthy_when_the_request_raises(self):
        import httpx

        provider = _provider()
        with patch.object(provider.client, "get", side_effect=httpx.ConnectError("refused")):
            assert provider.health_check() is False

    def test_defaults_supports_speech_rate_to_true_before_any_check(self):
        assert _provider().supports_speech_rate is True

    def test_updates_supports_speech_rate_from_the_health_response(self):
        provider = _provider()
        fake_resp = MagicMock(status_code=200)
        fake_resp.json.return_value = {"status": "ok", "engine": "chatterbox", "supports_speech_rate": False}
        with patch.object(provider.client, "get", return_value=fake_resp):
            provider.health_check()
        assert provider.supports_speech_rate is False

    def test_leaves_supports_speech_rate_unset_when_the_response_omits_it(self):
        provider = _provider()
        fake_resp = MagicMock(status_code=200)
        fake_resp.json.return_value = {"status": "ok"}
        with patch.object(provider.client, "get", return_value=fake_resp):
            provider.health_check()
        assert provider.supports_speech_rate is True

    def test_does_not_update_supports_speech_rate_on_a_failed_check(self):
        provider = _provider()
        fake_resp = MagicMock(status_code=200)
        fake_resp.json.return_value = {"status": "ok", "supports_speech_rate": False}
        with patch.object(provider.client, "get", return_value=fake_resp):
            provider.health_check()
        assert provider.supports_speech_rate is False

        with patch.object(provider.client, "get", return_value=MagicMock(status_code=503)):
            provider.health_check()
        assert provider.supports_speech_rate is False

    def test_defaults_supports_exaggeration_to_false_before_any_check(self):
        assert _provider().supports_exaggeration is False

    def test_updates_supports_exaggeration_from_the_health_response(self):
        provider = _provider()
        fake_resp = MagicMock(status_code=200)
        fake_resp.json.return_value = {"status": "ok", "engine": "chatterbox", "supports_exaggeration": True}
        with patch.object(provider.client, "get", return_value=fake_resp):
            provider.health_check()
        assert provider.supports_exaggeration is True

    def test_leaves_supports_exaggeration_unset_when_the_response_omits_it(self):
        provider = _provider()
        fake_resp = MagicMock(status_code=200)
        fake_resp.json.return_value = {"status": "ok"}
        with patch.object(provider.client, "get", return_value=fake_resp):
            provider.health_check()
        assert provider.supports_exaggeration is False


class TestTTSFactoryNetworkProvider:
    def test_selects_network_provider_when_configured(self, monkeypatch):
        from app.config import get_settings
        from app.services.tts.factory import get_tts_provider

        settings = get_settings()
        monkeypatch.setattr(settings, "tts_provider", "network")
        monkeypatch.setattr(settings, "tts_service_url", "http://tts.test:8100")
        get_tts_provider.cache_clear()
        try:
            provider = get_tts_provider()
            assert isinstance(provider, NetworkTTSProvider)
            assert provider.base_url == "http://tts.test:8100"
        finally:
            get_tts_provider.cache_clear()

    def test_raises_without_a_configured_service_url(self, monkeypatch):
        from app.config import get_settings
        from app.services.tts.factory import get_tts_provider

        settings = get_settings()
        monkeypatch.setattr(settings, "tts_provider", "network")
        monkeypatch.setattr(settings, "tts_service_url", "")
        get_tts_provider.cache_clear()
        try:
            with pytest.raises(ValueError, match="TTS_SERVICE_URL"):
                get_tts_provider()
        finally:
            get_tts_provider.cache_clear()

    def test_explicit_provider_name_overrides_the_global_default(self, monkeypatch, tmp_path):
        # A per-host tts_provider pin should work even when it's not the
        # deployment's global Settings.tts_provider.
        from app.config import get_settings
        from app.services.tts.factory import get_tts_provider
        from app.services.tts.piper_provider import PiperProvider

        settings = get_settings()
        monkeypatch.setattr(settings, "tts_provider", "network")
        monkeypatch.setattr(settings, "tts_service_url", "http://tts.test:8100")
        monkeypatch.setattr(settings, "piper_model_dir", str(tmp_path))
        get_tts_provider.cache_clear()
        try:
            default_provider = get_tts_provider()
            explicit_piper = get_tts_provider("piper")
            assert isinstance(default_provider, NetworkTTSProvider)
            assert isinstance(explicit_piper, PiperProvider)
        finally:
            get_tts_provider.cache_clear()

    def test_none_provider_name_resolves_to_the_global_default(self, monkeypatch):
        # NOTE: lru_cache keys on the literal call signature, so
        # get_tts_provider(None) and get_tts_provider() land in separate
        # cache slots even though they resolve to the same provider type --
        # a harmless minor duplication (cheap constructors, no shared state
        # that would actually go stale across the two instances), not
        # asserted here as an identity check.
        from app.config import get_settings
        from app.services.tts.factory import get_tts_provider
        from app.services.tts.network_provider import NetworkTTSProvider

        settings = get_settings()
        monkeypatch.setattr(settings, "tts_provider", "network")
        monkeypatch.setattr(settings, "tts_service_url", "http://tts.test:8100")
        get_tts_provider.cache_clear()
        try:
            assert isinstance(get_tts_provider(None), NetworkTTSProvider)
            assert isinstance(get_tts_provider(), NetworkTTSProvider)
        finally:
            get_tts_provider.cache_clear()

    def test_distinct_provider_names_are_cached_separately(self, monkeypatch, tmp_path):
        from app.config import get_settings
        from app.services.tts.factory import get_tts_provider

        settings = get_settings()
        monkeypatch.setattr(settings, "tts_service_url", "http://tts.test:8100")
        monkeypatch.setattr(settings, "piper_model_dir", str(tmp_path))
        get_tts_provider.cache_clear()
        try:
            assert get_tts_provider("piper") is get_tts_provider("piper")
            assert get_tts_provider("piper") is not get_tts_provider("network")
        finally:
            get_tts_provider.cache_clear()

    def test_explicit_network_still_raises_without_a_configured_service_url(self, monkeypatch):
        from app.config import get_settings
        from app.services.tts.factory import get_tts_provider

        settings = get_settings()
        monkeypatch.setattr(settings, "tts_provider", "piper")
        monkeypatch.setattr(settings, "tts_service_url", "")
        get_tts_provider.cache_clear()
        try:
            with pytest.raises(ValueError, match="TTS_SERVICE_URL"):
                get_tts_provider("network")
        finally:
            get_tts_provider.cache_clear()
