import ast
import json
import logging
import re
from abc import ABC, abstractmethod
from json_repair import repair_json
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# Shared field descriptions and category-matching guidance, reused across all
# classification prompts so wording stays consistent and changes apply everywhere.
CATEGORIES_FIELD = (
    '- "categories": array of category names taken verbatim from the provided list whose subject this '
    'item is genuinely about (can be empty [], can have multiple matches). '
    'ONLY use names that appear exactly in the list — do not invent new categories.'
)

RELEVANCE_FIELD = (
    '- "relevance_score": integer 1-10 — how central a matched category\'s subject is '
    'to this item: 10 = the item is principally about that subject, 1 = the subject is '
    'only briefly or tangentially mentioned. Use 5 if no category matched.'
)

CATEGORY_GUIDANCE = """Available categories (use ONLY these exact names): {categories_json}
Each category has a name, optional "keywords" (signals for its topic, not phrases that must appear verbatim) and optionally a "description". When a description is present, weigh it more heavily than the keywords. Judge fit by the item's overall subject, not incidental keyword overlap — only include a category if the item's main topic genuinely falls within it, even if a keyword appears only in passing. If no category fits, return an empty array."""


SYSTEM_PROMPT = """You are a neutral news analyst. Given a news article title and content, return a JSON object with exactly these fields:
- "abstract": string, 1-3 sentence factual summary based strictly on the provided title and content. Write in neutral, precise, journalistic language — no emotional qualifiers, value judgements, or editorialising. Do not add, infer, or embellish anything not explicitly stated in the source.
- "keywords": array of 3-7 short lowercase keywords or keyphrases in English (regardless of the article's language) that best represent the article's topic (e.g. ["llm", "openai", "reasoning models"])
{categories_field}
{relevance_field}
- "impact_score": integer 1-10, how broadly impactful this news is (10 = global significance, 1 = minor local event)

{category_guidance}

Respond ONLY with valid JSON. No markdown fences, no extra text.""".format(
    categories_field=CATEGORIES_FIELD, relevance_field=RELEVANCE_FIELD, category_guidance=CATEGORY_GUIDANCE,
)

SOCIAL_SYSTEM_PROMPT = """You are a neutral news analyst. Given a social media post, return a JSON object with exactly these fields:
- "headline": string, a short factual headline (max 12 words) that captures the core topic of the post.
- "abstract": string, 1-2 sentence factual summary based strictly on the post content. Write in neutral, precise language — no emotional qualifiers or editorialising. Do not add, infer, or embellish anything not explicitly stated.
- "keywords": array of 3-7 short lowercase keywords or keyphrases in English (regardless of the post's language) that best represent the post's topic.
{categories_field}
{relevance_field}
- "impact_score": integer 1-10, how broadly impactful this post is (10 = global significance, 1 = minor personal post)

{category_guidance}

Respond ONLY with valid JSON. No markdown fences, no extra text.""".format(
    categories_field=CATEGORIES_FIELD, relevance_field=RELEVANCE_FIELD, category_guidance=CATEGORY_GUIDANCE,
)


SHORT_ITEM_SYSTEM_PROMPT = """You are a news classifier. The news item below is very short — do not rewrite or summarise it. Extract metadata only.

Return a JSON object with exactly these fields:
- "keywords": array of 3-7 short lowercase keywords or keyphrases in English (regardless of the item's language) that best represent the topic
{categories_field}
{relevance_field}
- "impact_score": integer 1-10, how broadly impactful this is (10 = global significance, 1 = minor local event)

{category_guidance}

Respond ONLY with valid JSON. No markdown fences, no extra text.""".format(
    categories_field=CATEGORIES_FIELD, relevance_field=RELEVANCE_FIELD, category_guidance=CATEGORY_GUIDANCE,
)


MULTI_ITEM_SYSTEM_PROMPT = """You are a neutral news analyst. Analyse each news item below and return a JSON array — one object per item.

Each object must contain:
- "id": the item identifier exactly as given
- "abstract": string, 1-3 sentence factual summary in neutral, precise, journalistic language — no emotional qualifiers, value judgements, or editorialising
- "keywords": array of 3-7 short lowercase keywords or keyphrases in English (regardless of the item's language)
{categories_field}
{relevance_field}
- "impact_score": integer 1-10, how broadly impactful (10 = global significance, 1 = minor local event)

{category_guidance}

Respond ONLY with a valid JSON array. No markdown fences, no extra text.""".format(
    categories_field=CATEGORIES_FIELD, relevance_field=RELEVANCE_FIELD, category_guidance=CATEGORY_GUIDANCE,
)


MULTI_SHORT_ITEM_SYSTEM_PROMPT = """You are a news classifier. For each item below, extract metadata only — do not summarise.

Return a JSON array — one object per item — each containing:
- "id": the item identifier exactly as given
- "keywords": array of 3-7 short lowercase keywords or keyphrases in English (regardless of the item's language)
{categories_field}
{relevance_field}
- "impact_score": integer 1-10

{category_guidance}

Respond ONLY with a valid JSON array. No markdown fences, no extra text.""".format(
    categories_field=CATEGORIES_FIELD, relevance_field=RELEVANCE_FIELD, category_guidance=CATEGORY_GUIDANCE,
)


MULTI_SOCIAL_SYSTEM_PROMPT = """You are a news analyst. For each social media post below, return a JSON array — one object per post.

Each object must contain:
- "id": the item identifier exactly as given
- "headline": short punchy headline (max 12 words) capturing the core topic
- "abstract": string, 1-2 sentence summary
- "keywords": array of 3-7 short lowercase keywords or keyphrases in English (regardless of the item's language)
{categories_field}
{relevance_field}
- "impact_score": integer 1-10

{category_guidance}

Respond ONLY with a valid JSON array. No markdown fences, no extra text.""".format(
    categories_field=CATEGORIES_FIELD, relevance_field=RELEVANCE_FIELD, category_guidance=CATEGORY_GUIDANCE,
)


CLUSTER_SYSTEM_PROMPT = """You are a neutral news analyst. Multiple sources have covered the same event. Return a JSON object with exactly these fields:
- "source_summaries": object where each key is "item_0", "item_1", etc. — one entry per source. For each, write a short phrase (max 20 words) capturing what that source uniquely contributes: a specific fact, statistic, named person, quote, location detail, or angle not present in the others. Set a key to null only when a source genuinely adds nothing beyond what the other sources already cover. State the content directly — e.g. "Cites unnamed Pentagon official; 12% GDP impact estimate", "Only source to quote the opposition leader" — never begin with "This source", "Reports that", "Adds", "Highlights", "Notes", "States", "Also covers", or similar preamble.
- "title": string, a short factual headline (max 10 words) that captures the core event.
- "unified_abstract": string, 1-3 sentence factual summary that synthesises all sources into one coherent account, based strictly on the provided content. Write in neutral, precise, journalistic language — no emotional qualifiers, value judgements, or editorialising. Do not add or infer anything not present in the sources.
- "keywords": array of 3-7 short lowercase keywords or keyphrases in English (regardless of source language) that best represent this event (e.g. ["trade war", "tariffs", "eu"])
{categories_field}
{relevance_field}
- "impact_score": integer 1-10, how broadly impactful this event is

{category_guidance}

Respond ONLY with valid JSON. No markdown fences, no extra text.""".format(
    categories_field=CATEGORIES_FIELD, relevance_field=RELEVANCE_FIELD, category_guidance=CATEGORY_GUIDANCE,
)


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
    "uk": "Ukrainian",
}


def language_suffix(output_language: str | None, translate_title: bool = False) -> str:
    """Return a prompt suffix controlling output language for all generated text fields."""
    fields = "(title, abstract, unified_abstract, headline, summary, source_summaries)"
    if not output_language:
        return (
            f"\n\nIMPORTANT: All generated text fields {fields} "
            f"MUST be written in the same language as the source article(s). Do not translate."
        )
    name = LANGUAGE_NAMES.get(output_language, output_language)
    suffix = (
        f"\n\nIMPORTANT: All generated text fields {fields} "
        f"MUST be written in grammatically correct, standard {name}, regardless of the article's original language."
    )
    if translate_title:
        suffix += f'\nAlso include a "translated_title" field: the article title translated into {name}.'
    return suffix


@dataclass
class ProcessedResult:
    abstract: str
    keywords: list[str]
    category_names: list[str]
    relevance_score: int
    impact_score: int
    generated_title: str | None = None
    provider_name: str = ""
    model_name: str = ""


@dataclass
class ClusterResult:
    unified_abstract: str
    keywords: list[str]
    category_names: list[str]
    relevance_score: int
    impact_score: int
    title: str | None = None
    source_summaries: dict[str, str] = field(default_factory=dict)
    provider_name: str = ""
    model_name: str = ""


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
    provider_name: str = ""
    model_name: str = ""


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
    lookup = {name.casefold(): name for name in known_categories}
    result = []
    for n in raw:
        if isinstance(n, dict):
            n = n.get("name", "")
        elif isinstance(n, str) and n.strip().startswith("{"):
            try:
                parsed = ast.literal_eval(n.strip())
                if isinstance(parsed, dict):
                    n = parsed.get("name", "")
            except (ValueError, SyntaxError):
                pass
        name = str(n).strip()
        if not name:
            continue
        match = lookup.get(name.casefold())
        if match is None:
            logger.warning("LLM returned unrecognised category %r (known: %s)", name, known_categories)
            continue
        if match not in result:
            result.append(match)
    return result


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
    if social_post:
        generated_title = str(data["headline"]).strip() if data.get("headline") else None
    else:
        generated_title = str(data["translated_title"]).strip() if data.get("translated_title") else None

    return ProcessedResult(
        abstract=abstract,
        keywords=_parse_keywords(data.get("keywords")),
        category_names=category_names,
        relevance_score=_clamp(data.get("relevance_score"), 5),
        impact_score=_clamp(data.get("impact_score"), 5),
        generated_title=generated_title,
    )


def parse_short_llm_response(text: str, known_categories: list[str]) -> ProcessedResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(repair_json(text))

    raw_cats = data.get("categories", data.get("category"))
    return ProcessedResult(
        abstract="",  # caller fills this from the original content
        keywords=_parse_keywords(data.get("keywords")),
        category_names=_parse_categories(raw_cats, known_categories),
        relevance_score=_clamp(data.get("relevance_score"), 5),
        impact_score=_clamp(data.get("impact_score"), 5),
    )


# Matches LLM outputs like "same as item_0", "identical to item 1", "see item_2", etc.
_SAME_AS_RE = re.compile(
    r"\b(same\s+as|identical\s+to|no\s+different|see\s+item|identical\s+content)\b",
    re.IGNORECASE,
)
# Common filler preambles the LLM tends to produce even when told not to
_PREAMBLE_RE = re.compile(
    r"^(this\s+source\b|unlike\s+(other\s+sources?|others?)\b|this\s+article\b|focuses?\s+on\b"
    r"|reports?\s+that\b|adds?\s+that\b|highlights?\b|notes?\s+that\b|states?\s+that\b"
    r"|provides?\b|also\s+(covers?|includes?|reports?|mentions?)\b|uniquely\s+|the\s+(source|article)\b)",
    re.IGNORECASE,
)


def _clean_source_summary(val) -> str:
    if not val or not isinstance(val, str):
        return ""
    text = val.strip()
    if _SAME_AS_RE.search(text):
        return ""
    # Strip leading preambles iteratively — handles chains like "Unlike other sources, this article focuses on …"
    for _ in range(4):
        stripped = _PREAMBLE_RE.sub("", text).strip(" ,;:—-")
        if stripped == text:
            break
        text = stripped
    if text:
        text = text[0].upper() + text[1:]
    return text


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
        f"item_{i}": _clean_source_summary(raw.get(f"item_{i}"))
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


def parse_multi_item_response(
    text: str,
    known_categories: list[str],
    is_short: bool = False,
    is_social: bool = False,
) -> dict[str, "ProcessedResult"]:
    """Parse a multi-item LLM response. Returns a dict keyed by item id."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(repair_json(text))

    if not isinstance(data, list):
        return {}

    results: dict[str, ProcessedResult] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        item_id = str(entry.get("id", "")).strip()
        if not item_id:
            continue
        raw_cats = entry.get("categories", entry.get("category"))
        category_names = _parse_categories(raw_cats, known_categories)

        if is_short:
            result = ProcessedResult(
                abstract="",
                keywords=_parse_keywords(entry.get("keywords")),
                category_names=category_names,
                relevance_score=_clamp(entry.get("relevance_score"), 5),
                impact_score=_clamp(entry.get("impact_score"), 5),
            )
        else:
            if is_social:
                generated_title = str(entry["headline"]).strip() if entry.get("headline") else None
            else:
                generated_title = str(entry["translated_title"]).strip() if entry.get("translated_title") else None
            result = ProcessedResult(
                abstract=str(entry.get("abstract", "")).strip() or "No abstract available.",
                keywords=_parse_keywords(entry.get("keywords")),
                category_names=category_names,
                relevance_score=_clamp(entry.get("relevance_score"), 5),
                impact_score=_clamp(entry.get("impact_score"), 5),
                generated_title=generated_title,
            )
        results[item_id] = result
    return results


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
- "headline": the article title (max 15 words)
- "url": the article URL (tracking/redirect URLs are fine; set null only if truly absent)
- "summary": 1-3 sentence factual summary in neutral, precise, journalistic language — no emotional qualifiers or editorialising
- "keywords": array of 3-5 lowercase keywords in English (regardless of the article's language)
{categories_field}
{relevance_field}
- "impact_score": integer 1-10

Wrap the results in a JSON object with a single key "items" containing the array described above.

{category_guidance}

Rules:
- Skip ads, sponsored content, navigation, footer items, and subscription prompts
- Process every TITLE block — do not skip any

Respond ONLY with valid JSON. No markdown fences, no extra text.""".format(
    categories_field=CATEGORIES_FIELD, relevance_field=RELEVANCE_FIELD, category_guidance=CATEGORY_GUIDANCE,
)


def parse_newsletter_response(text: str, known_categories: list[str]) -> NewsletterResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(repair_json(text))
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


def parse_scraper_selector_response(text: str) -> dict:
    """Parse an LLM response suggesting CSS selectors for the web scraper.
    Raises ValueError if no usable item_selector was returned."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(repair_json(text))

    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")

    item_selector = str(data.get("item_selector") or "").strip()
    if not item_selector:
        raise ValueError("LLM response is missing item_selector")

    title_selector = str(data.get("title_selector") or "").strip() or "h1,h2,h3"
    link_selector = str(data.get("link_selector") or "").strip() or "a"
    content_selector = data.get("content_selector")
    content_selector = str(content_selector).strip() or None if content_selector else None

    return {
        "item_selector": item_selector,
        "title_selector": title_selector,
        "link_selector": link_selector,
        "content_selector": content_selector,
    }


def dedup_cluster_payload(
    items: list[dict],
    max_content_chars: int = 800,
) -> tuple[list[dict], list[int | None]]:
    """Deduplicate cluster items by content before sending to the LLM.

    Returns:
        dedup_items  — unique items to send (subset of `items`)
        orig_to_dedup — for each original item index, its index in dedup_items,
                        or None if it is a duplicate (identical content to an earlier item)
    """
    seen: dict[str, int] = {}
    dedup_items: list[dict] = []
    orig_to_dedup: list[int | None] = []

    for item in items:
        key = (item.get("content") or item.get("title", ""))[:max_content_chars]
        if key in seen:
            orig_to_dedup.append(None)
        else:
            idx = len(dedup_items)
            seen[key] = idx
            orig_to_dedup.append(idx)
            dedup_items.append(item)

    return dedup_items, orig_to_dedup


SCRAPER_SELECTOR_PROMPT = """You are configuring a web scraper for a news aggregator. Below is a simplified version of a webpage's HTML — scripts, styles, and most attributes have been removed, and text has been shortened, so you can focus on the structure.

Page URL: {url}

Simplified HTML:
{html}

Find the repeated structural pattern used for each article/post/link in a list of items on this page. Return a JSON object with exactly these fields:
- "item_selector": a CSS selector that matches EACH item container (must match multiple elements on this page)
- "title_selector": a CSS selector, relative to the item container, for the element holding the item's title/headline
- "link_selector": a CSS selector, relative to the item container, for the <a> element linking to the full article
- "content_selector": a CSS selector, relative to the item container, for an element with a summary/description/snippet, or null if there isn't one

Rules:
- Selectors must be valid CSS and should work with Python's BeautifulSoup `select()`.
- Avoid class names containing characters that need escaping in CSS (colons, slashes, etc. — common in utility-class frameworks like Tailwind, e.g. "hover:bg-gray-100" or "lg:w-1/2"). Prefer tag names, simple class names, or attribute selectors instead.
- Prefer selectors based on semantic, repeated patterns rather than brittle deep positional paths.

Respond ONLY with valid JSON. No markdown fences, no extra text."""


CATEGORY_PROMPT_GENERATION = """Write a classification prompt for the news category "{name}".{keywords_section}{other_categories_section}

The prompt will be read by an LLM that assigns news articles to categories.
Structure it as:
1. One concise sentence stating what articles belong here
2. Two to four concrete signals (entities, topics, terms, institutions) that indicate a clear match
3. One "Do not assign if…" clause for the most likely confusion

Under {max_chars} characters total. Output ONLY the prompt text — no labels, no preamble, no explanation."""


class LLMProvider(ABC):
    provider_name: str = ""
    model_name: str = ""

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

    def process_short_item(
        self,
        title: str,
        content: str,
        categories: list[dict],
    ) -> ProcessedResult:
        """Classify a short item (≤40 words): extract keywords/categories only, no abstract generation."""
        known = [c["name"] for c in categories]
        system = SHORT_ITEM_SYSTEM_PROMPT.format(categories_json=json.dumps(categories, ensure_ascii=False))
        user = f"Title: {title}\nContent: {content}" if content.strip() else f"Title: {title}"
        text = self._complete(system=system, user=user, max_tokens=256)
        result = parse_short_llm_response(text, known)
        result.provider_name = self.provider_name
        result.model_name = self.model_name
        return result

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

    def suggest_scraper_selectors(self, url: str, html: str, feedback: str | None = None) -> str:
        user = SCRAPER_SELECTOR_PROMPT.format(url=url, html=html)
        if feedback:
            user += f"\n\n{feedback}"
        return self._complete(
            system="You are a precise web scraping configuration assistant. Respond only with JSON.",
            user=user,
            max_tokens=300,
        )

    def generate_category_prompt(
        self,
        name: str,
        keywords: list[str],
        existing_categories: list[str] | None = None,
        max_chars: int = 500,
    ) -> str:
        kw_section = (
            f"\nUser-provided keywords (hints only): {', '.join(keywords)}."
            if keywords else ""
        )
        other_cats = [c for c in (existing_categories or []) if c.lower() != name.lower()][:20]
        cats_section = (
            "\nOther categories already in this system (use for the disambiguation clause):\n"
            + "\n".join(f"- {c}" for c in other_cats)
            if other_cats else ""
        )
        result = self._complete(
            system="You are a precise prompt engineer for news categorisation systems.",
            user=CATEGORY_PROMPT_GENERATION.format(
                name=name,
                keywords_section=kw_section,
                other_categories_section=cats_section,
                max_chars=max_chars,
            ),
            max_tokens=300,
        )
        return result[:max_chars]

    @abstractmethod
    def health_check(self) -> bool: ...
