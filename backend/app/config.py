from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    database_url: str = "postgresql+psycopg://phoenix:changeme@localhost:5432/phoenix"
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "ShoebillFeed/1.0"
    reddit_username: str = ""
    reddit_password: str = ""

    youtube_api_key: str = ""

    llm_batch_max_wait_minutes: int = 10

    jwt_secret: str = "change-me-in-production"
    jwt_expire_hours: int = 168  # 7 days
    admin_username: str = ""
    admin_password: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
