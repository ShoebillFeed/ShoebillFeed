import redis as redis_lib
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import get_settings
from app.schemas.news_item import HealthOut, LLMConfigOut, LLMConfigUpdate
from app.services.llm.factory import get_llm_provider

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health_check(db: Session = Depends(get_db)):
    db_ok = False
    redis_ok = False
    llm_ok = False

    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        settings = get_settings()
        r = redis_lib.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        redis_ok = True
    except Exception:
        pass

    try:
        provider = get_llm_provider()
        llm_ok = provider.health_check()
    except Exception:
        pass

    return HealthOut(db=db_ok, redis=redis_ok, llm=llm_ok)


@router.get("/llm", response_model=LLMConfigOut)
def get_llm_config():
    settings = get_settings()
    return LLMConfigOut(
        llm_provider=settings.llm_provider,
        anthropic_model=settings.anthropic_model,
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
    )


@router.patch("/llm", response_model=LLMConfigOut)
def update_llm_config(payload: LLMConfigUpdate):
    # In a containerised setup, provider config comes from env vars.
    # This endpoint reports back the current effective config;
    # actual changes require updating .env and restarting the service.
    settings = get_settings()
    return LLMConfigOut(
        llm_provider=payload.llm_provider or settings.llm_provider,
        anthropic_model=payload.anthropic_model or settings.anthropic_model,
        ollama_base_url=payload.ollama_base_url or settings.ollama_base_url,
        ollama_model=payload.ollama_model or settings.ollama_model,
    )
