from functools import lru_cache
from app.config import get_settings
from app.services.llm.base import LLMProvider


def _build_provider(name: str, settings) -> LLMProvider:
    if name == "anthropic":
        from app.services.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
    if name == "ollama":
        from app.services.llm.ollama_provider import OllamaProvider
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout=settings.ollama_timeout,
        )
    raise ValueError(f"Unknown LLM provider: {name!r}")


@lru_cache(maxsize=1)
def _get_provider_instances() -> dict[str, LLMProvider]:
    """Build one instance per named provider, cached for the process lifetime."""
    settings = get_settings()
    instances: dict[str, LLMProvider] = {}
    for name in settings.llm_provider_list:
        if name not in instances:
            instances[name] = _build_provider(name, settings)
    return instances


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Returns a FallbackProvider wrapping all configured providers in priority order."""
    settings = get_settings()
    instances = _get_provider_instances()
    ordered = [instances[n] for n in settings.llm_provider_list if n in instances]
    if not ordered:
        raise ValueError("No valid LLM providers configured in LLM_PROVIDERS")
    if len(ordered) == 1:
        return ordered[0]
    from app.services.llm.fallback_provider import FallbackProvider
    return FallbackProvider(ordered)


def get_anthropic_provider():
    """Returns the AnthropicProvider instance if configured, else None.
    Use this for Anthropic Batch API calls — do not use get_llm_provider() for those."""
    return _get_provider_instances().get("anthropic")
