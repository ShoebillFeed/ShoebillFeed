import pytest

from app.config import get_settings
from app.engines.factory import get_engine
from app.engines.kokoro_engine import KokoroEngine
from app.engines.piper_engine import PiperEngine


@pytest.fixture(autouse=True)
def _clear_engine_cache():
    get_engine.cache_clear()
    yield
    get_engine.cache_clear()


def test_selects_piper_engine_by_default(monkeypatch, tmp_path):
    settings = get_settings()
    monkeypatch.setattr(settings, "tts_engine", "piper")
    monkeypatch.setattr(settings, "tts_model_dir", str(tmp_path))
    monkeypatch.setattr(settings, "tts_device", "cpu")

    engine = get_engine()

    assert isinstance(engine, PiperEngine)
    assert engine.use_cuda is False


def test_use_cuda_true_when_device_is_cuda(monkeypatch, tmp_path):
    settings = get_settings()
    monkeypatch.setattr(settings, "tts_engine", "piper")
    monkeypatch.setattr(settings, "tts_model_dir", str(tmp_path))
    monkeypatch.setattr(settings, "tts_device", "cuda")

    engine = get_engine()

    assert engine.use_cuda is True


def test_selects_kokoro_engine(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "tts_engine", "kokoro")
    monkeypatch.setattr(settings, "tts_device", "cpu")

    engine = get_engine()

    assert isinstance(engine, KokoroEngine)
    assert engine.use_cuda is False


def test_kokoro_use_cuda_true_when_device_is_cuda(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "tts_engine", "kokoro")
    monkeypatch.setattr(settings, "tts_device", "cuda")

    engine = get_engine()

    assert engine.use_cuda is True


def test_unknown_engine_raises(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "tts_engine", "bogus")

    with pytest.raises(ValueError, match="TTS_ENGINE"):
        get_engine()
