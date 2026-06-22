import json
import httpx

from app.services.llm.base import (
    LLMProvider, ProcessedResult, ClusterResult, NewsletterResult,
    SYSTEM_PROMPT, SOCIAL_SYSTEM_PROMPT, CLUSTER_SYSTEM_PROMPT, NEWSLETTER_SYSTEM_PROMPT,
    parse_llm_response, parse_cluster_response, parse_newsletter_response,
    language_suffix,
)


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
        self.client = httpx.Client(timeout=float(timeout))

    def _post(self, payload: dict, timeout: float | None = None) -> dict:
        kw = {"timeout": timeout} if timeout is not None else {}
        resp = self.client.post(f"{self.base_url}/api/generate", json=payload, **kw)
        if resp.status_code == 400 and payload.get("think"):
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
            "options": {"num_predict": max_tokens, "temperature": 0.2},
        }
        return self._post(payload)["response"]

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
            "options": {"num_predict": 1024, "temperature": 0.2},
        }
        result = parse_llm_response(self._post(payload)["response"], known, social_post=social_post)
        result.provider_name = self.provider_name
        result.model_name = self.model_name
        return result

    def process_cluster(self, items, categories, max_content_chars=800, output_language=None) -> ClusterResult:
        known = [c["name"] for c in categories]
        system = CLUSTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories)) + language_suffix(output_language)

        parts = []
        for i, item in enumerate(items):
            content = (item.get("content") or item["title"])[:max_content_chars]
            parts.append(f"Item {i} (Source: {item['source_name']}):\nTitle: {item['title']}\nContent: {content}")

        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "keep_alive": self.KEEP_ALIVE,
            "format": "json",
            "system": system,
            "prompt": "\n\n".join(parts),
            "options": {"num_predict": 2048, "temperature": 0.2},
        }
        result = parse_cluster_response(self._post(payload)["response"], len(items), known)
        result.provider_name = self.provider_name
        result.model_name = self.model_name
        return result

    def extract_newsletter_items(self, content: str, categories: list[dict], output_language=None) -> NewsletterResult:
        known = [c["name"] for c in categories]
        system = NEWSLETTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories, ensure_ascii=False)) + language_suffix(output_language)
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "keep_alive": self.KEEP_ALIVE,
            "format": "json",
            "system": system,
            "prompt": f"Newsletter content:\n\n{content[:8000]}",
            "options": {"num_predict": 4096, "temperature": 0.2},
        }
        result = parse_newsletter_response(self._post(payload, timeout=600.0)["response"], known)
        result.provider_name = self.provider_name
        result.model_name = self.model_name
        return result

    def health_check(self) -> bool:
        try:
            resp = self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
