import json
import anthropic

from app.services.llm.base import (
    LLMProvider, ProcessedResult, ClusterResult, NewsletterResult,
    SYSTEM_PROMPT, SOCIAL_SYSTEM_PROMPT, CLUSTER_SYSTEM_PROMPT, NEWSLETTER_SYSTEM_PROMPT,
    parse_llm_response, parse_cluster_response, parse_newsletter_response,
)


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text

    def process_item(self, title, content, categories, max_content_chars=4000, social_post=False) -> ProcessedResult:
        truncated = (content or title)[:max_content_chars]
        known = [c["name"] for c in categories]
        prompt_template = SOCIAL_SYSTEM_PROMPT if social_post else SYSTEM_PROMPT
        system = prompt_template.format(categories_json=json.dumps(categories))
        user = f"Post: {truncated}" if social_post else f"Title: {title}\n\nContent: {truncated}"

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return parse_llm_response(message.content[0].text, known, social_post=social_post)

    def process_cluster(self, items, categories, max_content_chars=2000) -> ClusterResult:
        known = [c["name"] for c in categories]
        system = CLUSTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories))

        parts = []
        for i, item in enumerate(items):
            content = (item.get("content") or item["title"])[:max_content_chars]
            parts.append(f"Item {i} (Source: {item['source_name']}):\nTitle: {item['title']}\nContent: {content}")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": "\n\n".join(parts)}],
        )
        return parse_cluster_response(message.content[0].text, len(items), known)

    def extract_newsletter_items(self, content: str, categories: list[dict]) -> NewsletterResult:
        known = [c["name"] for c in categories]
        system = NEWSLETTER_SYSTEM_PROMPT.format(categories_json=json.dumps(categories, ensure_ascii=False))
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": f"Newsletter content:\n\n{content[:8000]}"}],
        )
        return parse_newsletter_response(message.content[0].text, known)

    def health_check(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False
