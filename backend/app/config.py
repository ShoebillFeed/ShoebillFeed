from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    database_url: str = "postgresql+psycopg://phoenix:changeme@localhost:5432/phoenix"
    redis_url: str = "redis://localhost:6379/0"

    # Ordered, comma-separated provider list. First = primary, rest = fallbacks.
    # Valid names: anthropic, ollama
    # Accepts both LLM_PROVIDERS and LLM_PROVIDER (legacy singular name).
    # Example: LLM_PROVIDERS=anthropic,ollama
    llm_providers: str = Field(
        default="anthropic",
        validation_alias=AliasChoices("llm_providers", "llm_provider"),
    )
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"
    # Set to a remote host to use Ollama on another machine, e.g. http://192.168.1.10:11434
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_timeout: int = 300  # seconds; increase for remote/slow hosts

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "ShoebillFeed/1.0"
    reddit_username: str = ""
    reddit_password: str = ""

    llm_batch_max_wait_minutes: int = 10

    jwt_secret: str = "change-me-in-production"
    jwt_expire_hours: int = 24
    admin_username: str = ""
    admin_password: str = ""

    # Web Push (VAPID) — generate keys with: python -c "from pywebpush import Vapid; v=Vapid(); v.generate_keys(); print('VAPID_PRIVATE_KEY='+v.private_key); print('VAPID_PUBLIC_KEY='+v.public_key)"
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@localhost"

    # Podcast text-to-speech provider: 'piper' (in-process, self-hosted CPU/ONNX)
    # or 'network' (talks to a standalone tts_service/ container -- see
    # docker-compose.tts.yml -- so synthesis can run on a different machine,
    # e.g. one with a GPU).
    tts_provider: str = "piper"
    piper_model_dir: str = "/data/piper-voices"
    podcast_audio_dir: str = "/data/podcast-audio"
    tts_service_url: str = ""
    tts_service_timeout: float = 120.0

    # Spoken-words-per-minute used to size podcast scripts (both the LLM's
    # word-count target and how many stories get selected for a given target
    # length). Default (210) was measured against Piper's
    # en_US-libritts_r-medium voice -- see PODCAST_WORDS_PER_MINUTE in
    # services/llm/base.py. Kokoro and Chatterbox speak at a different
    # natural pace (Chatterbox noticeably slower and more variable in
    # particular); if TTS_PROVIDER/TTS_ENGINE isn't Piper, tune this to match
    # your engine's actual measured pace rather than trusting the default.
    podcast_words_per_minute: int = 210

    # Required to enable a podcast show's public feed link (RSS enclosure/link
    # URLs must be fully-qualified for podcast apps to consume them). No
    # trailing slash, e.g. https://shoebill.example.com
    public_base_url: str = ""


    @property
    def llm_provider(self) -> str:
        """Primary provider name (first entry in llm_providers)."""
        return self.llm_providers.split(",")[0].strip()

    @property
    def llm_provider_list(self) -> list[str]:
        return [p.strip() for p in self.llm_providers.split(",") if p.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
