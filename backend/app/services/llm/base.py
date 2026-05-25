import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


SYSTEM_PROMPT = """You are a news analyst. Given a news article title and content, return a JSON object with exactly these fields:
- "abstract": string, 2-4 sentence summary of the article. Write the abstract in the same language as the article.
- "keywords": array of 3-7 short lowercase keywords or keyphrases that best represent the article's topic (e.g. ["llm", "openai", "reasoning models"])
- "categories": array of category names from the provided list that fit this article (can be empty [], can have multiple matches)
- "relevance_score": integer 1-10, how relevant this is to the matched categories' keywords (5 if no category matched)
- "impact_score": integer 1-10, how broadly impactful this news is (10 = global significance, 1 = minor local event)

Available categories: {categories_json}
Each category has a name and keywords. If a description field is present, use it to judge whether the article fits that category. Include all categories that genuinely apply.

Respond ONLY with valid JSON. No markdown fences, no extra text."""


CLUSTER_SYSTEM_PROMPT = """You are a news analyst. Multiple sources have covered the same event. Return a JSON object with exactly these fields:
- "unified_abstract": string, 2-4 sentence summary that synthesises all sources into one coherent account. Write in the same language as the source articles.
- "keywords": array of 3-7 short lowercase keywords or keyphrases that best represent this event (e.g. ["trade war", "tariffs", "eu"])
- "categories": array of category names from the provided list that fit this event (can be empty [], can have multiple matches)
- "relevance_score": integer 1-10
- "impact_score": integer 1-10, how broadly impactful this event is
- "source_summaries": object where each key is "item_0", "item_1", etc. and each value is a 1-2 sentence description of how that source's angle or emphasis differs from the others

Available categories: {categories_json}
Each category has a name and keywords. If a description field is present, use it to judge whether the article fits that category. Include all categories that genuinely apply.

Respond ONLY with valid JSON. No markdown fences, no extra text."""


@dataclass
class ProcessedResult:
    abstract: str
    keywords: list[str]
    category_names: list[str]
    relevance_score: int
    impact_score: int


@dataclass
class ClusterResult:
    unified_abstract: str
    keywords: list[str]
    category_names: list[str]
    relevance_score: int
    impact_score: int
    source_summaries: dict[str, str] = field(default_factory=dict)


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


def parse_llm_response(text: str, known_categories: list[str]) -> ProcessedResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)

    abstract = str(data.get("abstract", "")).strip() or "No abstract available."
    # Accept both "categories" (new) and legacy "category" (single string)
    raw_cats = data.get("categories", data.get("category"))
    category_names = _parse_categories(raw_cats, known_categories)

    return ProcessedResult(
        abstract=abstract,
        keywords=_parse_keywords(data.get("keywords")),
        category_names=category_names,
        relevance_score=_clamp(data.get("relevance_score"), 5),
        impact_score=_clamp(data.get("impact_score"), 5),
    )


def parse_cluster_response(text: str, item_count: int, known_categories: list[str]) -> ClusterResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)

    abstract = str(data.get("unified_abstract", "")).strip() or "No summary available."
    raw_cats = data.get("categories", data.get("category"))
    category_names = _parse_categories(raw_cats, known_categories)

    raw = data.get("source_summaries", {})
    source_summaries = {
        f"item_{i}": str(raw.get(f"item_{i}", "")).strip()
        for i in range(item_count)
    }

    return ClusterResult(
        unified_abstract=abstract,
        keywords=_parse_keywords(data.get("keywords")),
        category_names=category_names,
        relevance_score=_clamp(data.get("relevance_score"), 5),
        impact_score=_clamp(data.get("impact_score"), 5),
        source_summaries=source_summaries,
    )


CATEGORY_TOPICS_PROMPT = """What topics, themes, subtopics, and related keywords typically appear in news coverage under the category "{name}"?{keywords_hint}

List them concisely — no preamble, no explanation, just the topics and keywords."""

CATEGORY_PROMPT_GENERATION = """You are configuring a news categorization system.

Category name: "{name}"
Topics and keywords that belong in this category:
{topics}

Write a 2-4 sentence classification prompt that tells an LLM when to assign a news article to this category. It should describe what kinds of articles belong here and what signals (topics, terms, contexts) indicate a match.

Return ONLY the classification prompt — no labels, no reasoning, no extra text."""


class LLMProvider(ABC):
    @abstractmethod
    def process_item(
        self,
        title: str,
        content: str,
        categories: list[dict],
        max_content_chars: int = 4000,
    ) -> ProcessedResult: ...

    @abstractmethod
    def process_cluster(
        self,
        items: list[dict],
        categories: list[dict],
        max_content_chars: int = 2000,
    ) -> ClusterResult: ...

    @abstractmethod
    def _complete(self, system: str, user: str, max_tokens: int = 512) -> str: ...

    def generate_category_prompt(self, name: str, keywords: list[str]) -> str:
        keywords_hint = (
            f"\nThe user has provided these seed keywords as hints: {', '.join(keywords)}."
            if keywords else ""
        )
        topics = self._complete(
            system="You are a concise knowledge assistant.",
            user=CATEGORY_TOPICS_PROMPT.format(name=name, keywords_hint=keywords_hint),
        )
        return self._complete(
            system="You are a precise prompt engineer for news categorization systems.",
            user=CATEGORY_PROMPT_GENERATION.format(name=name, topics=topics.strip()),
        )

    @abstractmethod
    def health_check(self) -> bool: ...
