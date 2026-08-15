from functools import lru_cache

from app.config import get_settings
from app.engines.base import TTSEngine


@lru_cache(maxsize=1)
def get_engine() -> TTSEngine:
    settings = get_settings()
    use_cuda = settings.tts_device == "cuda"
    if settings.tts_engine == "piper":
        from app.engines.piper_engine import PiperEngine
        return PiperEngine(model_dir=settings.tts_model_dir, use_cuda=use_cuda)
    if settings.tts_engine == "kokoro":
        from app.engines.kokoro_engine import KokoroEngine
        return KokoroEngine(use_cuda=use_cuda)
    if settings.tts_engine == "chatterbox":
        from app.engines.chatterbox_engine import ChatterboxEngine
        return ChatterboxEngine(model_dir=settings.tts_model_dir, use_cuda=use_cuda)
    raise ValueError(f"Unknown TTS_ENGINE: {settings.tts_engine!r}")
