from functools import lru_cache
from app.config import get_settings
from app.services.tts.base import TTSProvider


@lru_cache(maxsize=1)
def get_tts_provider() -> TTSProvider:
    settings = get_settings()
    if settings.tts_provider == "piper":
        from app.services.tts.piper_provider import PiperProvider
        return PiperProvider(model_dir=settings.piper_model_dir)
    raise ValueError(f"Unknown TTS provider: {settings.tts_provider!r}")
