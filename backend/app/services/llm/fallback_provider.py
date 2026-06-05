import logging
from app.services.llm.base import LLMProvider, ProcessedResult, ClusterResult, NewsletterResult

logger = logging.getLogger(__name__)


class FallbackProvider(LLMProvider):
    """Tries each provider in order, falling back to the next on any exception."""

    def __init__(self, providers: list[LLMProvider]):
        self._providers = providers

    def _try(self, method: str, *args, **kwargs):
        last_exc: Exception | None = None
        for provider in self._providers:
            try:
                return getattr(provider, method)(*args, **kwargs)
            except Exception as exc:
                logger.warning(
                    "LLM provider %s failed on %s (%s), trying next",
                    type(provider).__name__, method, exc,
                )
                last_exc = exc
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
