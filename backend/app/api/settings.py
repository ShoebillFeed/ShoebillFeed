import redis as redis_lib
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.config import get_settings
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.news_item import HealthOut, LLMConfigOut, LLMConfigUpdate, ProviderInfo, ProviderHealth
from app.schemas.user_settings import UserSettingsOut, UserSettingsUpdate
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
    finally:
        # Nothing below needs the DB. Release the pooled connection now
        # instead of holding it for the redis ping + LLM health checks
        # (which can each take several seconds) -- otherwise, under load,
        # this endpoint alone can help exhaust the pool since it's hit
        # repeatedly by the Docker healthcheck every 30s regardless of
        # what else is happening on the same worker.
        db.close()

    try:
        settings = get_settings()
        r = redis_lib.from_url(settings.redis_url, socket_connect_timeout=2)
        try:
            r.ping()
            redis_ok = True
        finally:
            r.close()
    except Exception:
        pass

    provider_health: list[ProviderHealth] = []
    try:
        from app.services.llm.factory import _get_provider_instances
        instances = _get_provider_instances()
        for name, p in instances.items():
            try:
                healthy = p.health_check()
            except Exception:
                healthy = False
            provider_health.append(ProviderHealth(name=name, healthy=healthy))
        llm_ok = any(ph.healthy for ph in provider_health)
    except Exception:
        pass

    return HealthOut(db=db_ok, redis=redis_ok, llm=llm_ok, provider_health=provider_health)


def _build_llm_config() -> LLMConfigOut:
    settings = get_settings()
    providers = []
    for i, name in enumerate(settings.llm_provider_list):
        info = ProviderInfo(name=name, is_primary=(i == 0))
        if name == "anthropic":
            info.model = settings.anthropic_model
        elif name == "ollama":
            info.model = settings.ollama_model
            info.base_url = settings.ollama_base_url
        providers.append(info)
    return LLMConfigOut(providers=providers)


@router.get("/llm", response_model=LLMConfigOut)
def get_llm_config():
    return _build_llm_config()


@router.patch("/llm", response_model=LLMConfigOut)
def update_llm_config(payload: LLMConfigUpdate):
    # Config is read-only via API; changes require updating .env and restarting.
    return _build_llm_config()


def _get_or_create_settings(db: Session, user_id) -> UserSettings:
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/advanced", response_model=UserSettingsOut)
def get_advanced_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_or_create_settings(db, current_user.id)


@router.patch("/advanced", response_model=UserSettingsOut)
def update_advanced_settings(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = _get_or_create_settings(db, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s
