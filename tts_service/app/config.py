from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Which synthesis backend to run. Only "piper" exists today; this is the
    # hook for adding another self-hostable engine (e.g. Kokoro) later
    # without changing the HTTP API or Shoebill's own client.
    tts_engine: str = "piper"

    # "cpu" or "cuda". Requires the image to have been built with
    # TTS_GPU=true (installs onnxruntime-gpu) and the container run with
    # GPU access (--gpus / the compose file's NVIDIA deploy block) --
    # setting this without either of those does nothing useful.
    tts_device: str = "cpu"

    tts_model_dir: str = "/data/voices"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
