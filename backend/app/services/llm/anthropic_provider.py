import json
import anthropic

from app.services.llm.base import (
    LLMProvider, ProcessedResult, ClusterResult, NewsletterResult,
    SYSTEM_PROMPT, SOCIAL_SYSTEM_PROMPT, SHORT_ITEM_SYSTEM_PROMPT,
    MULTI_ITEM_SYSTEM_PROMPT, MULTI_SHORT_ITEM_SYSTEM_PROMPT, MULTI_SOCIAL_SYSTEM_PROMPT,
    CLUSTER_SYSTEM_PROMPT, NEWSLETTER_SYSTEM_PROMPT,
    parse_llm_response, parse_cluster_response, parse_newsletter_response,
    language_suffix,
)


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=self._cached_system(system),
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text

    def _cached_system(self, text: str) -> list[dict]:
        """Wrap a system prompt for Anthropic prompt caching.
        Identical prompts within the 5-minute cache window cost ~10% of normal input price."""
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    def process_item(self, title, content, categories, max_content_chars=1500, social_post=False, output_language=None) -> ProcessedResult:
        truncated = (content or title)[:max_content_chars]
        known = [c["name"] for c in categories]
        prompt_template = SOCIAL_SYSTEM_PROMPT if social_post else SYSTEM_PROMPT
        system = prompt_template.format(categories_json=json.dumps(categories)) + language_suffix(output_language)
        user = f"Post: {truncated}" if social_post else f"Title: {title}\n\nContent: {truncated}"

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self._cached_system(system),
            messages=[{"role": "user", "content": user}],
        )
        return parse_llm_response(message.content[0].text, known, social_post=social_post)

    def process_cluster(self, items, categories, max_content_chars=800, output_language=None) -> ClusterResult:
        known = [c["name"] for c in categories]
        system = CLUSTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories)) + language_suffix(output_language)

        parts = []
        for i, item in enumerate(items):
            content = (item.get("content") or item["title"])[:max_content_chars]
            parts.append(f"Item {i} (Source: {item['source_name']}):\nTitle: {item['title']}\nContent: {content}")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self._cached_system(system),
            messages=[{"role": "user", "content": "\n\n".join(parts)}],
        )
        return parse_cluster_response(message.content[0].text, len(items), known)

    def extract_newsletter_items(self, content: str, categories: list[dict], output_language=None) -> NewsletterResult:
        known = [c["name"] for c in categories]
        system = NEWSLETTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories, ensure_ascii=False)) + language_suffix(output_language)
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._cached_system(system),
            messages=[{"role": "user", "content": f"Newsletter content:\n\n{content[:4000]}"}],
        )
        return parse_newsletter_response(message.content[0].text, known)

    def build_item_request(
        self,
        custom_id: str,
        title: str,
        content: str,
        categories: list[dict],
        is_short: bool = False,
        social_post: bool = False,
        output_language: str | None = None,
        max_content_chars: int = 1500,
    ) -> dict:
        """Return a batch request dict (no API call)."""
        if is_short:
            system = SHORT_ITEM_SYSTEM_PROMPT.format(categories_json=json.dumps(categories, ensure_ascii=False))
            user = f"Title: {title}\nContent: {content}" if content.strip() else f"Title: {title}"
            max_tokens = 256
        else:
            truncated = (content or title)[:max_content_chars]
            prompt_template = SOCIAL_SYSTEM_PROMPT if social_post else SYSTEM_PROMPT
            system = prompt_template.format(categories_json=json.dumps(categories)) + language_suffix(output_language)
            user = f"Post: {truncated}" if social_post else f"Title: {title}\n\nContent: {truncated}"
            max_tokens = 1024
        return {
            "custom_id": custom_id,
            "params": {
                "model": self.model,
                "max_tokens": max_tokens,
                "system": self._cached_system(system),
                "messages": [{"role": "user", "content": user}],
            },
        }

    def build_multi_item_request(
        self,
        custom_id: str,
        items: list[dict],
        categories: list[dict],
        group_type: str = "full",
        output_language: str | None = None,
        max_content_chars: int = 1500,
    ) -> dict:
        """Return a batch request dict covering multiple items (no API call)."""
        if group_type == "short":
            system = MULTI_SHORT_ITEM_SYSTEM_PROMPT.format(categories_json=json.dumps(categories, ensure_ascii=False))
            max_tokens = min(len(items) * 150, 2048)
        elif group_type == "social":
            system = MULTI_SOCIAL_SYSTEM_PROMPT.format(categories_json=json.dumps(categories)) + language_suffix(output_language)
            max_tokens = min(len(items) * 400, 4096)
        else:
            system = MULTI_ITEM_SYSTEM_PROMPT.format(categories_json=json.dumps(categories)) + language_suffix(output_language)
            max_tokens = min(len(items) * 400, 4096)

        parts = []
        for item in items:
            content = (item.get("content") or "").strip()
            if content:
                parts.append(f"[{item['id']}]\nTitle: {item['title']}\nContent: {content[:max_content_chars]}")
            else:
                parts.append(f"[{item['id']}]\nTitle: {item['title']}")

        return {
            "custom_id": custom_id,
            "params": {
                "model": self.model,
                "max_tokens": max_tokens,
                "system": self._cached_system(system),
                "messages": [{"role": "user", "content": "\n\n".join(parts)}],
            },
        }

    def build_cluster_request(
        self,
        custom_id: str,
        items: list[dict],
        categories: list[dict],
        output_language: str | None = None,
        max_content_chars: int = 800,
    ) -> dict:
        """Return a batch request dict (no API call)."""
        system = CLUSTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories)) + language_suffix(output_language)
        parts = []
        for i, item in enumerate(items):
            content = (item.get("content") or item["title"])[:max_content_chars]
            parts.append(f"Item {i} (Source: {item['source_name']}):\nTitle: {item['title']}\nContent: {content}")
        return {
            "custom_id": custom_id,
            "params": {
                "model": self.model,
                "max_tokens": 2048,
                "system": self._cached_system(system),
                "messages": [{"role": "user", "content": "\n\n".join(parts)}],
            },
        }

    def health_check(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False
