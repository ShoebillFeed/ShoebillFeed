import json
import httpx

from app.services.llm.base import (
    LLMProvider, ProcessedResult, ClusterResult, NewsletterResult,
    SYSTEM_PROMPT, SOCIAL_SYSTEM_PROMPT, CLUSTER_SYSTEM_PROMPT, NEWSLETTER_SYSTEM_PROMPT,
    parse_llm_response, parse_cluster_response, parse_newsletter_response,
    language_suffix,
)


def _num_ctx_for(system: str, user: str, max_tokens: int) -> int:
    """Ollama does not grow num_ctx to fit the prompt automatically -- a
    model's default context window (often 2048, and not always big enough
    even for e.g. the podcast script prompt's story content) silently
    truncates or empties the response when system+user text plus the
    requested output exceeds it, instead of erroring. ~3 chars/token is a
    deliberately conservative estimate (real English text averages closer to
    4) so this errs toward a larger window rather than an exact one.
    """
    estimated_prompt_tokens = (len(system) + len(user)) // 3
    return max(4096, estimated_prompt_tokens + max_tokens + 512)


# Conservative (slow-CPU) generation speed estimate, seconds per output token.
_SECONDS_PER_TOKEN_ESTIMATE = 0.2


def _timeout_for(max_tokens: int, floor: float) -> float:
    """Generation time scales with the requested output length, especially
    on CPU-only hosts -- a fixed client timeout sized for small
    classification calls gets hit by larger generations (e.g. the podcast
    script). This was most visible once _num_ctx_for started sizing the
    context window correctly: calls that used to fail fast with a
    silently-truncated response now actually run to completion, which takes
    real time. Real hardware is often faster than this estimate, which just
    means the request returns well before the deadline.
    """
    return max(floor, max_tokens * _SECONDS_PER_TOKEN_ESTIMATE)


class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    # Keep the model resident in VRAM between requests so the ~2-3s weight-load
    # cost isn't paid again on the first call of each processing batch (default
    # Ollama keep_alive is 5 minutes, shorter than the 15-minute process schedule).
    KEEP_ALIVE = "30m"

    def __init__(self, base_url: str, model: str = "qwen3:8b", timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.model_name = model
        self.default_timeout = float(timeout)
        self.client = httpx.Client(timeout=self.default_timeout)
        # Set once a `think: true` request 400s -- some models (e.g. gemma3)
        # don't support Ollama's think/no-think toggle at all, so every call
        # that opts into it would otherwise fail once and pay a full extra
        # round-trip on *every single request* for the life of the process,
        # not just the first. get_llm_provider() is lru_cached per process
        # (see llm/factory.py), so this instance -- and the flag -- lives
        # for the whole worker's lifetime, same scope the cache assumes.
        self._think_unsupported = False

    def _post(self, payload: dict, timeout: float | None = None) -> dict:
        kw = {"timeout": timeout} if timeout is not None else {}
        if self._think_unsupported and payload.get("think"):
            payload = {**payload, "think": False}
        resp = self.client.post(f"{self.base_url}/api/generate", json=payload, **kw)
        if resp.status_code == 400 and payload.get("think"):
            self._think_unsupported = True
            payload = {**payload, "think": False}
            resp = self.client.post(f"{self.base_url}/api/generate", json=payload, **kw)
        resp.raise_for_status()
        return resp.json()

    def _complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "keep_alive": self.KEEP_ALIVE,
            "format": "json",
            "system": system,
            "prompt": user,
            "options": {
                "num_predict": max_tokens,
                "num_ctx": _num_ctx_for(system, user, max_tokens),
                "temperature": 0.1,
            },
        }
        return self._post(payload, timeout=_timeout_for(max_tokens, self.default_timeout))["response"]

    def process_item(self, title, content, categories, max_content_chars=1500, social_post=False, output_language=None) -> ProcessedResult:
        truncated = (content or title)[:max_content_chars]
        known = [c["name"] for c in categories]
        prompt_template = SOCIAL_SYSTEM_PROMPT if social_post else SYSTEM_PROMPT
        system = prompt_template.format(categories_json=json.dumps(categories)) + language_suffix(output_language, translate_title=not social_post)
        user = f"Post: {truncated}" if social_post else f"Title: {title}\n\nContent: {truncated}"

        payload = {
            "model": self.model,
            "stream": False,
            "think": True,
            "keep_alive": self.KEEP_ALIVE,
            "format": "json",
            "system": system,
            "prompt": user,
            "options": {
                "num_predict": 1024,
                "num_ctx": _num_ctx_for(system, user, 1024),
                "temperature": 0.1,
            },
        }
        response = self._post(payload, timeout=_timeout_for(1024, self.default_timeout))["response"]
        result = parse_llm_response(response, known, social_post=social_post)
        result.provider_name = self.provider_name
        result.model_name = self.model_name
        return result

    def process_cluster(self, items, categories, max_content_chars=1200, output_language=None) -> ClusterResult:
        known = [c["name"] for c in categories]
        system = CLUSTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories)) + language_suffix(output_language)

        parts = []
        for i, item in enumerate(items):
            content = (item.get("content") or item["title"])[:max_content_chars]
            parts.append(f"Item {i} (Source: {item['source_name']}):\nTitle: {item['title']}\nContent: {content}")

        user = "\n\n".join(parts)
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "keep_alive": self.KEEP_ALIVE,
            "format": "json",
            "system": system,
            "prompt": user,
            "options": {
                "num_predict": 2048,
                "num_ctx": _num_ctx_for(system, user, 2048),
                "temperature": 0.1,
            },
        }
        response = self._post(payload, timeout=_timeout_for(2048, self.default_timeout))["response"]
        result = parse_cluster_response(response, len(items), known)
        result.provider_name = self.provider_name
        result.model_name = self.model_name
        return result

    def extract_newsletter_items(self, content: str, categories: list[dict], output_language=None) -> NewsletterResult:
        known = [c["name"] for c in categories]
        system = NEWSLETTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories, ensure_ascii=False)) + language_suffix(output_language)
        user = f"Newsletter content:\n\n{content[:8000]}"
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "keep_alive": self.KEEP_ALIVE,
            "format": "json",
            "system": system,
            "prompt": user,
            "options": {
                "num_predict": 4096,
                "num_ctx": _num_ctx_for(system, user, 4096),
                "temperature": 0.1,
            },
        }
        response = self._post(payload, timeout=_timeout_for(4096, self.default_timeout))["response"]
        result = parse_newsletter_response(response, known)
        result.provider_name = self.provider_name
        result.model_name = self.model_name
        return result

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass

    def health_check(self) -> bool:
        try:
            resp = self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
