from functools import lru_cache
from app.config import get_settings
from app.services.tts.base import TTSProvider


@lru_cache(maxsize=1)
def get_tts_provider() -> TTSProvider:
    settings = get_settings()
    if settings.tts_provider == "piper":
        from app.services.tts.piper_provider import PiperProvider
        return PiperProvider(model_dir=settings.piper_model_dir)
    if settings.tts_provider == "network":
        from app.services.tts.network_provider import NetworkTTSProvider
        if not settings.tts_service_url:
            raise ValueError("TTS_SERVICE_URL must be set when TTS_PROVIDER=network")
        return NetworkTTSProvider(base_url=settings.tts_service_url, timeout=settings.tts_service_timeout)
    raise ValueError(f"Unknown TTS provider: {settings.tts_provider!r}")
