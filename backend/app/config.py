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

    youtube_api_key: str = ""

    llm_batch_max_wait_minutes: int = 10

    jwt_secret: str = "change-me-in-production"
    jwt_expire_hours: int = 24
    admin_username: str = ""
    admin_password: str = ""

    # Web Push (VAPID) — generate keys with: python -c "from pywebpush import Vapid; v=Vapid(); v.generate_keys(); print('VAPID_PRIVATE_KEY='+v.private_key); print('VAPID_PUBLIC_KEY='+v.public_key)"
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@localhost"


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
