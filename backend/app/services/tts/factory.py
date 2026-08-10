from functools import lru_cache
from app.config import get_settings
from app.services.tts.base import TTSProvider


@lru_cache(maxsize=None)
def get_tts_provider(provider_name: str | None = None) -> TTSProvider:
    """Returns the TTSProvider for `provider_name` ("piper" or "network"), or
    the globally configured default (Settings.tts_provider) when not given.
    Each distinct name is constructed once and cached -- this is what lets a
    podcast host pin a specific engine (PodcastHostSchema.tts_provider)
    without disturbing the shared default instance every other caller
    (health checks, hosts with no explicit override) still relies on."""
    settings = get_settings()
    name = provider_name or settings.tts_provider
    if name == "piper":
        from app.services.tts.piper_provider import PiperProvider
        return PiperProvider(model_dir=settings.piper_model_dir)
    if name == "network":
        from app.services.tts.network_provider import NetworkTTSProvider
        if not settings.tts_service_url:
            raise ValueError("TTS_SERVICE_URL must be set to use the network TTS provider")
        return NetworkTTSProvider(base_url=settings.tts_service_url, timeout=settings.tts_service_timeout)
    raise ValueError(f"Unknown TTS provider: {name!r}")
