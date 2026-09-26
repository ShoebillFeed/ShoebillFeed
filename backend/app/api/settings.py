import redis as redis_lib
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.config import get_settings
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.news_item import (
    HealthOut, LLMConfigOut, LLMConfigUpdate, LLMUsageOut, ModelUsageOut,
    ProviderInfo, ProviderHealth, TTSHealthOut,
)
from app.schemas.user_settings import UserSettingsOut, UserSettingsUpdate
from app.services.llm.factory import get_llm_provider
from app.services.token_scopes import ALL_SCOPES

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


@router.get("/podcast-health", response_model=TTSHealthOut)
def podcast_health_check():
    # Matches /health and /llm above: unauthenticated, consistent with the
    # rest of this settings-diagnostics file (not a change introduced here).
    # Deliberately its own endpoint, not folded into /health: that one is
    # also hit by the docker-compose healthcheck every 30s, and a slow or
    # unreachable TTS_PROVIDER=network host would make the container's own
    # healthcheck flaky. This is only ever called on-demand from Settings.
    from app.services.tts.factory import get_tts_provider

    settings = get_settings()
    try:
        provider = get_tts_provider()
        healthy = provider.health_check()
        supports_speech_rate = provider.supports_speech_rate
        supports_exaggeration = provider.supports_exaggeration
        # Read after health_check(), not before: NetworkTTSProvider only
        # learns the remote engine's name from that call's /health response.
        engine = provider.engine
    except Exception:
        healthy = False
        supports_speech_rate = True
        supports_exaggeration = False
        engine = None

    return TTSHealthOut(
        provider=settings.tts_provider,
        healthy=healthy,
        base_url=settings.tts_service_url if settings.tts_provider == "network" else None,
        supports_speech_rate=supports_speech_rate,
        supports_exaggeration=supports_exaggeration,
        network_configured=bool(settings.tts_service_url),
        engine=engine,
    )


@router.get("/token-scopes")
def get_token_scopes(request: Request, current_user: User = Depends(get_current_user)):
    """What the *calling credential* is allowed to do.

    Lets an MCP client hide tools it cannot use. That is a usability layer,
    not a security boundary -- the boundary is the scope check in
    services/auth.py, which applies whether or not a client bothers to ask.

    Ungated on purpose (see token_scopes.py): a token restricted to, say,
    `read` still has to be able to discover that. A cookie session reports
    `scopes: null`, same as an unrestricted token, since scopes only ever
    limit tokens.
    """
    api_token = getattr(request.state, "api_token", None)
    return {
        "scopes": api_token.scopes if api_token else None,
        "all_scopes": [{"key": k, "description": d} for k, d in ALL_SCOPES.items()],
    }


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


@router.get("/llm-usage", response_model=LLMUsageOut)
def get_llm_usage():
    """How many requests each configured model actually handled, over
    rolling 1h/24h windows. Kept out of /llm because that one is static
    config the frontend fetches once, while this changes continuously and
    is refreshed alongside the health check."""
    from app.services.llm.usage import request_counts

    settings = get_settings()
    models: list[str] = []
    for name in settings.llm_provider_list:
        if name == "anthropic":
            models.append(settings.anthropic_model)
        elif name == "ollama":
            models.append(settings.ollama_model)

    # dict.fromkeys, not set(): two providers can be configured against the
    # same model name, and the panel should list it once, in config order.
    counts = request_counts(list(dict.fromkeys(models)))
    return LLMUsageOut(
        models=[
            ModelUsageOut(model=model, hour=c["hour"], day=c["day"])
            for model, c in counts.items()
        ]
    )


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
