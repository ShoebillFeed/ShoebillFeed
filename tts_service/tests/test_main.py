from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "ok", "engine": "piper", "supports_speech_rate": True, "supports_exaggeration": False,
    }


def test_health_reports_engine_name_and_capabilities():
    fake_engine = MagicMock()
    fake_engine.engine_name = "chatterbox"
    fake_engine.supports_speech_rate = False
    fake_engine.supports_exaggeration = True
    with patch("app.main.get_engine", return_value=fake_engine):
        resp = client.get("/health")

    assert resp.json() == {
        "status": "ok", "engine": "chatterbox", "supports_speech_rate": False, "supports_exaggeration": True,
    }


def test_list_voices_returns_engine_voices():
    from app.engines.base import VoiceInfo

    fake_engine = MagicMock()
    fake_engine.list_voices.return_value = [VoiceInfo(id="v1", language="en", label="Voice 1")]
    with patch("app.main.get_engine", return_value=fake_engine):
        resp = client.get("/voices", params={"language": "en"})

    assert resp.status_code == 200
    assert resp.json() == [{"id": "v1", "language": "en", "label": "Voice 1"}]
    fake_engine.list_voices.assert_called_once_with("en")


def test_list_voices_requires_language_query_param():
    resp = client.get("/voices")
    assert resp.status_code == 422


def test_synthesize_returns_wav_bytes_and_duration_header():
    fake_engine = MagicMock()
    fake_engine.synthesize.return_value = (b"RIFF....", 3.5)
    with patch("app.main.get_engine", return_value=fake_engine):
        resp = client.post("/synthesize", json={"text": "Hello", "voice_id": "v1", "speech_rate": 1.2})

    assert resp.status_code == 200
    assert resp.content == b"RIFF...."
    assert resp.headers["content-type"] == "audio/wav"
    assert resp.headers["x-duration-seconds"] == "3.5"
    fake_engine.synthesize.assert_called_once_with("Hello", "v1", 1.2, None)


def test_synthesize_defaults_speech_rate_to_one():
    fake_engine = MagicMock()
    fake_engine.synthesize.return_value = (b"bytes", 1.0)
    with patch("app.main.get_engine", return_value=fake_engine):
        client.post("/synthesize", json={"text": "Hi", "voice_id": "v1"})

    fake_engine.synthesize.assert_called_once_with("Hi", "v1", 1.0, None)


def test_synthesize_passes_exaggeration_through():
    fake_engine = MagicMock()
    fake_engine.synthesize.return_value = (b"bytes", 1.0)
    with patch("app.main.get_engine", return_value=fake_engine):
        client.post("/synthesize", json={"text": "Hi", "voice_id": "v1", "exaggeration": 0.8})

    fake_engine.synthesize.assert_called_once_with("Hi", "v1", 1.0, 0.8)


def test_synthesize_returns_400_for_a_value_error():
    fake_engine = MagicMock()
    fake_engine.synthesize.side_effect = ValueError("Unknown Piper voice model: 'bogus'")
    with patch("app.main.get_engine", return_value=fake_engine):
        resp = client.post("/synthesize", json={"text": "Hi", "voice_id": "bogus"})

    assert resp.status_code == 400


def test_synthesize_returns_500_on_unexpected_engine_error():
    fake_engine = MagicMock()
    fake_engine.synthesize.side_effect = RuntimeError("boom")
    with patch("app.main.get_engine", return_value=fake_engine):
        resp = client.post("/synthesize", json={"text": "Hi", "voice_id": "v1"})

    assert resp.status_code == 500


def test_synthesize_requires_non_empty_text():
    resp = client.post("/synthesize", json={"text": "", "voice_id": "v1"})
    assert resp.status_code == 422
