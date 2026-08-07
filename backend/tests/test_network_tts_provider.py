import os
from unittest.mock import MagicMock, patch

import pytest

from app.services.tts.network_provider import NetworkTTSProvider


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
            "text": "Hello there", "voice_id": "en_US-libritts_r-medium#0", "speech_rate": 1.5,
        }
        assert os.path.exists(out_path)
        with open(out_path, "rb") as f:
            assert f.read() == b"RIFF....fake wav bytes"
        assert result.audio_path == out_path
        assert result.duration_seconds == 4.2

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
