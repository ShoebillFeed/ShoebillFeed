import json
import httpx

from app.services.llm.base import (
    LLMProvider, ProcessedResult, ClusterResult,
    SYSTEM_PROMPT, CLUSTER_SYSTEM_PROMPT,
    parse_llm_response, parse_cluster_response,
)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str = "qwen2.5:0.5b"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=120.0)

    def _complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "system": system,
            "prompt": user,
            "options": {"num_predict": max_tokens},
        }
        resp = self.client.post(f"{self.base_url}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]

    def process_item(self, title, content, categories, max_content_chars=4000) -> ProcessedResult:
        truncated = (content or title)[:max_content_chars]
        known = [c["name"] for c in categories]
        system = SYSTEM_PROMPT.format(categories_json=json.dumps(categories))

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "system": system,
            "prompt": f"Title: {title}\n\nContent: {truncated}",
        }
        resp = self.client.post(f"{self.base_url}/api/generate", json=payload)
        resp.raise_for_status()
        return parse_llm_response(resp.json()["response"], known)

    def process_cluster(self, items, categories, max_content_chars=2000) -> ClusterResult:
        known = [c["name"] for c in categories]
        system = CLUSTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories))

        parts = []
        for i, item in enumerate(items):
            content = (item.get("content") or item["title"])[:max_content_chars]
            parts.append(f"Item {i} (Source: {item['source_name']}):\nTitle: {item['title']}\nContent: {content}")

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "system": system,
            "prompt": "\n\n".join(parts),
        }
        resp = self.client.post(f"{self.base_url}/api/generate", json=payload)
        resp.raise_for_status()
        return parse_cluster_response(resp.json()["response"], len(items), known)

    def health_check(self) -> bool:
        try:
            resp = self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
