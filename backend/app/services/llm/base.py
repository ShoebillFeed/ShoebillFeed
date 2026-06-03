import json
from abc import ABC, abstractmethod
from json_repair import repair_json
from dataclasses import dataclass, field
from typing import Optional


SYSTEM_PROMPT = """You are a news analyst. Given a news article title and content, return a JSON object with exactly these fields:
- "abstract": string, 2-4 sentence summary of the article. Write the abstract in the same language as the article.
- "keywords": array of 3-7 short lowercase keywords or keyphrases that best represent the article's topic (e.g. ["llm", "openai", "reasoning models"])
- "categories": array of category names from the provided list that fit this article (can be empty [], can have multiple matches)
- "relevance_score": integer 1-10, how relevant this is to the matched categories' keywords (5 if no category matched)
- "impact_score": integer 1-10, how broadly impactful this news is (10 = global significance, 1 = minor local event)

Available categories: {categories_json}
Each category has a name and keywords. If a description field is present, use it to judge whether the article fits that category. Include all categories that genuinely apply.

Respond ONLY with valid JSON. No markdown fences, no extra text."""

SOCIAL_SYSTEM_PROMPT = """You are a news analyst. Given a social media post, return a JSON object with exactly these fields:
- "headline": string, a short punchy headline (max 12 words) that captures the core topic of the post. Write in the same language as the post.
- "abstract": string, 1-2 sentence summary of the post. Write in the same language as the post.
- "keywords": array of 3-7 short lowercase keywords or keyphrases that best represent the post's topic.
- "categories": array of category names from the provided list that fit this post (can be empty [], can have multiple matches)
- "relevance_score": integer 1-10, how relevant this is to the matched categories' keywords (5 if no category matched)
- "impact_score": integer 1-10, how broadly impactful this post is (10 = global significance, 1 = minor personal post)

Available categories: {categories_json}
Each category has a name and keywords. If a description field is present, use it to judge whether the post fits that category. Include all categories that genuinely apply.

Respond ONLY with valid JSON. No markdown fences, no extra text."""


CLUSTER_SYSTEM_PROMPT = """You are a news analyst. Multiple sources have covered the same event. Return a JSON object with exactly these fields:
- "title": string, a short headline (max 10 words) that captures the core event. Write in the same language as the source articles.
- "unified_abstract": string, 2-4 sentence summary that synthesises all sources into one coherent account. Write in the same language as the source articles.
- "keywords": array of 3-7 short lowercase keywords or keyphrases that best represent this event (e.g. ["trade war", "tariffs", "eu"])
- "categories": array of category names from the provided list that fit this event (can be empty [], can have multiple matches)
- "relevance_score": integer 1-10
- "impact_score": integer 1-10, how broadly impactful this event is
- "source_summaries": object where each key is "item_0", "item_1", etc. and each value is a 1-2 sentence description of how that source's angle or emphasis differs from the others

Available categories: {categories_json}
Each category has a name and keywords. If a description field is present, use it to judge whether the article fits that category. Include all categories that genuinely apply.

Respond ONLY with valid JSON. No markdown fences, no extra text."""


LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ar": "Arabic",
    "ko": "Korean",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "nb": "Norwegian",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
}


def language_suffix(output_language: str | None) -> str:
    """Return a prompt suffix that forces a specific output language, or empty string."""
    if not output_language:
        return ""
    name = LANGUAGE_NAMES.get(output_language, output_language)
    return (
        f"\n\nIMPORTANT: All generated text fields "
        f"(abstract, unified_abstract, headline, summary, source_summaries) "
        f"MUST be written in {name}, regardless of the article's original language."
    )


@dataclass
class ProcessedResult:
    abstract: str
    keywords: list[str]
    category_names: list[str]
    relevance_score: int
    impact_score: int
    generated_title: str | None = None


@dataclass
class ClusterResult:
    unified_abstract: str
    keywords: list[str]
    category_names: list[str]
    relevance_score: int
    impact_score: int
    title: str | None = None
    source_summaries: dict[str, str] = field(default_factory=dict)


@dataclass
class NewsletterItem:
    headline: str
    url: Optional[str]
    summary: str
    keywords: list[str]
    category_names: list[str]
    relevance_score: int
    impact_score: int


@dataclass
class NewsletterResult:
    items: list[NewsletterItem]


def _clamp(v, default: int = 5) -> int:
    try:
        return max(1, min(10, int(v)))
    except (TypeError, ValueError):
        return default


def _parse_keywords(raw) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(k).strip().lower() for k in raw if str(k).strip()][:10]


def _parse_categories(raw, known_categories: list[str]) -> list[str]:
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    return [name for name in (str(n).strip() for n in raw) if name in known_categories]


def parse_llm_response(text: str, known_categories: list[str], social_post: bool = False) -> ProcessedResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(repair_json(text))

    abstract = str(data.get("abstract", "")).strip() or "No abstract available."
    raw_cats = data.get("categories", data.get("category"))
    category_names = _parse_categories(raw_cats, known_categories)
    generated_title = str(data["headline"]).strip() if social_post and data.get("headline") else None

    return ProcessedResult(
        abstract=abstract,
        keywords=_parse_keywords(data.get("keywords")),
        category_names=category_names,
        relevance_score=_clamp(data.get("relevance_score"), 5),
        impact_score=_clamp(data.get("impact_score"), 5),
        generated_title=generated_title,
    )


def parse_cluster_response(text: str, item_count: int, known_categories: list[str]) -> ClusterResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(repair_json(text))

    title = str(data.get("title", "")).strip() or None
    abstract = str(data.get("unified_abstract", "")).strip() or "No summary available."
    raw_cats = data.get("categories", data.get("category"))
    category_names = _parse_categories(raw_cats, known_categories)

    raw = data.get("source_summaries", {})
    source_summaries = {
        f"item_{i}": str(raw.get(f"item_{i}", "")).strip()
        for i in range(item_count)
    }

    return ClusterResult(
        title=title,
        unified_abstract=abstract,
        keywords=_parse_keywords(data.get("keywords")),
        category_names=category_names,
        relevance_score=_clamp(data.get("relevance_score"), 5),
        impact_score=_clamp(data.get("impact_score"), 5),
        source_summaries=source_summaries,
    )


NEWSLETTER_SYSTEM_PROMPT = """You are a newsletter parser. Extract individual news items from newsletter content.

The content may appear in two formats:

FORMAT A — Pre-extracted article blocks (each separated by a blank line):
  TITLE: <headline>
  URL: <link to full article>
  TEASER: <short description>  (optional)

FORMAT B — Raw text with inline [link text](url) markers:
  Article headings appear before links labelled "weiterlesen", "read more", etc.
  Those links are the article URLs.

For each article, return one object with:
- "headline": the article title, in the same language as the content (max 15 words)
- "url": the article URL (tracking/redirect URLs are fine; set null only if truly absent)
- "summary": 1-3 sentence summary in the same language
- "keywords": array of 3-5 lowercase keywords
- "categories": array of matching category names from the list (can be [])
- "relevance_score": integer 1-10
- "impact_score": integer 1-10

Return: {{"items": [...]}}

Available categories: {categories_json}

Rules:
- Skip ads, sponsored content, navigation, footer items, and subscription prompts
- Process every TITLE block — do not skip any

Respond ONLY with valid JSON. No markdown fences, no extra text."""


def parse_newsletter_response(text: str, known_categories: list[str]) -> NewsletterResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    raw_items = data.get("items", [])
    if not isinstance(raw_items, list):
        return NewsletterResult(items=[])

    items = []
    for entry in raw_items:
        if not isinstance(entry, dict):
            continue
        headline = str(entry.get("headline", "")).strip()
        if not headline:
            continue
        url = entry.get("url")
        url = str(url).strip() if url and str(url).strip().startswith("http") else None
        summary = str(entry.get("summary", "")).strip() or None
        items.append(NewsletterItem(
            headline=headline,
            url=url,
            summary=summary,
            keywords=_parse_keywords(entry.get("keywords")),
            category_names=_parse_categories(entry.get("categories", []), known_categories),
            relevance_score=_clamp(entry.get("relevance_score"), 5),
            impact_score=_clamp(entry.get("impact_score"), 5),
        ))
    return NewsletterResult(items=items)


CATEGORY_TOPICS_PROMPT = """What topics, themes, subtopics, and related keywords typically appear in news coverage under the category "{name}"?{keywords_hint}

List them concisely — no preamble, no explanation, just the topics and keywords."""

CATEGORY_PROMPT_GENERATION = """You are configuring a news categorization system.

Category name: "{name}"
Topics and keywords that belong in this category:
{topics}

Write a classification prompt that tells an LLM when to assign a news article to this category. It should describe what kinds of articles belong here and what signals (topics, terms, contexts) indicate a match.
Keep it under {max_chars} characters. Be concise — 2-3 sentences maximum.

Return ONLY the classification prompt — no labels, no reasoning, no extra text."""


class LLMProvider(ABC):
    @abstractmethod
    def process_item(
        self,
        title: str,
        content: str,
        categories: list[dict],
        max_content_chars: int = 4000,
        social_post: bool = False,
        output_language: str | None = None,
    ) -> ProcessedResult: ...

    @abstractmethod
    def process_cluster(
        self,
        items: list[dict],
        categories: list[dict],
        max_content_chars: int = 2000,
        output_language: str | None = None,
    ) -> ClusterResult: ...

    @abstractmethod
    def extract_newsletter_items(
        self,
        content: str,
        categories: list[dict],
        output_language: str | None = None,
    ) -> NewsletterResult: ...

    @abstractmethod
    def _complete(self, system: str, user: str, max_tokens: int = 512) -> str: ...

    def generate_category_prompt(self, name: str, keywords: list[str], max_chars: int = 500) -> str:
        keywords_hint = (
            f"\nThe user has provided these seed keywords as hints: {', '.join(keywords)}."
            if keywords else ""
        )
        topics = self._complete(
            system="You are a concise knowledge assistant.",
            user=CATEGORY_TOPICS_PROMPT.format(name=name, keywords_hint=keywords_hint),
        )
        result = self._complete(
            system="You are a precise prompt engineer for news categorization systems.",
            user=CATEGORY_PROMPT_GENERATION.format(name=name, topics=topics.strip(), max_chars=max_chars),
        )
        return result[:max_chars]

    @abstractmethod
    def health_check(self) -> bool: ...
