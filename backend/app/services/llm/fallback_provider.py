import logging
import time

from app.services.llm.base import LLMProvider, ProcessedResult, ClusterResult, NewsletterResult

logger = logging.getLogger(__name__)

# Attempts per provider before moving to the next one.
# 2 = one retry: try once, wait, try again, then fall through.
_ATTEMPTS_PER_PROVIDER = 2
_RETRY_DELAY_S = 5.0


class FallbackProvider(LLMProvider):
    """Tries each provider in order, retrying once before falling back to the next."""

    def __init__(self, providers: list[LLMProvider]):
        self._providers = providers

    def _try(self, method: str, *args, **kwargs):
        last_exc: Exception | None = None
        for provider in self._providers:
            name = type(provider).__name__
            for attempt in range(1, _ATTEMPTS_PER_PROVIDER + 1):
                try:
                    return getattr(provider, method)(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < _ATTEMPTS_PER_PROVIDER:
                        logger.warning(
                            "LLM %s failed on %s (attempt %d/%d): %s — retrying in %.0fs",
                            name, method, attempt, _ATTEMPTS_PER_PROVIDER, exc, _RETRY_DELAY_S,
                        )
                        time.sleep(_RETRY_DELAY_S)
                    else:
                        logger.warning(
                            "LLM %s failed on %s after %d attempt(s): %s — trying next provider",
                            name, method, attempt, exc,
                        )
        raise last_exc  # type: ignore[misc]

    def _complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        return self._try("_complete", system, user, max_tokens)

    def process_item(self, title, content, categories, max_content_chars=1500, social_post=False, output_language=None) -> ProcessedResult:
        return self._try("process_item", title, content, categories, max_content_chars, social_post, output_language)

    def process_cluster(self, items, categories, max_content_chars=800, output_language=None) -> ClusterResult:
        return self._try("process_cluster", items, categories, max_content_chars, output_language)

    def extract_newsletter_items(self, content, categories, output_language=None) -> NewsletterResult:
        return self._try("extract_newsletter_items", content, categories, output_language)

    def health_check(self) -> bool:
        return any(p.health_check() for p in self._providers)
