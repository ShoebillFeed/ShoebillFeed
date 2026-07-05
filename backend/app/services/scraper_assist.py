import json
import logging
import re

from bs4 import BeautifulSoup, Comment

from app.services.fetchers.scraper import fetch_html, parse_scraper_items
from app.services.llm.base import parse_scraper_selector_response
from app.services.llm.factory import get_llm_provider

logger = logging.getLogger(__name__)

SIMPLIFY_MAX_CHARS = 12000
PREVIEW_LIMIT = 8

_KEEP_ATTRS = {"class", "id", "href"}
_TEXT_SNIPPET_LEN = 80
_HREF_SNIPPET_LEN = 60
_MAX_CLASSES = 3

# Chrome-level noise that never contains article listings and can consume
# thousands of characters before the real content begins.
_NOISE_TAGS = [
    "script", "style", "svg", "noscript", "head", "iframe", "template",
    "nav", "header", "footer", "aside", "form",
]


def _simplify_html(html: str, max_chars: int = SIMPLIFY_MAX_CHARS) -> str:
    """Strip a page down to its tag/class/id/href structure with short text
    snippets, so an LLM can spot the repeated article pattern cheaply.

    Navigation, headers, footers, sidebars and forms are removed first because
    they sit at the top of the DOM and push article content past the character
    budget.  The search then scopes to <main> or <article> when present, since
    those elements almost always wrap the listing we care about.
    """
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(_NOISE_TAGS):
        tag.decompose()
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    # Prefer the main content block; fall back to the full body.
    body = soup.find("main") or soup.find("article") or soup.body or soup

    for tag in body.find_all(True):
        attrs = {k: v for k, v in tag.attrs.items() if k in _KEEP_ATTRS}
        classes = attrs.get("class")
        if isinstance(classes, list):
            attrs["class"] = " ".join(classes[:_MAX_CLASSES])
        href = attrs.get("href")
        if isinstance(href, str) and len(href) > _HREF_SNIPPET_LEN:
            attrs["href"] = href[:_HREF_SNIPPET_LEN] + "…"
        tag.attrs = attrs

    for node in body.find_all(string=True):
        text = re.sub(r"\s+", " ", str(node)).strip()
        if not text:
            node.extract()
        elif len(text) > _TEXT_SNIPPET_LEN:
            node.replace_with(text[:_TEXT_SNIPPET_LEN] + "…")
        else:
            node.replace_with(text)

    result = str(body)
    if len(result) > max_chars:
        result = result[:max_chars]
    return result


def suggest_scraper_config(url: str) -> dict:
    """Fetch a page and ask the configured LLM to identify CSS selectors for
    its article list, then validate the suggestion against the real page.

    Raises on fetch errors. Returns a dict with the suggested config, a
    preview of matched items, and the total item_count (0 if nothing matched).
    """
    html = fetch_html(url)
    simplified = _simplify_html(html)

    provider = get_llm_provider()
    raw = provider.suggest_scraper_selectors(url=url, html=simplified)
    config = parse_scraper_selector_response(raw)
    items = parse_scraper_items(html, base_url=url, **config)

    if not items:
        logger.info("Scraper suggestion %r matched 0 items on %s, retrying", config, url)
        feedback = (
            f"Your previous suggestion {json.dumps(config)} matched 0 items on this page. "
            "Try different, more general selectors."
        )
        raw = provider.suggest_scraper_selectors(url=url, html=simplified, feedback=feedback)
        retry_config = parse_scraper_selector_response(raw)
        retry_items = parse_scraper_items(html, base_url=url, **retry_config)
        if retry_items:
            config, items = retry_config, retry_items

    preview = [
        {"title": i.title, "url": i.url, "content": i.raw_content[:120].strip() if i.raw_content else ""}
        for i in items[:PREVIEW_LIMIT]
    ]
    return {
        "config": {
            "url": url,
            "item_selector": config["item_selector"],
            "title_selector": config["title_selector"],
            "link_selector": config["link_selector"],
            "content_selector": config["content_selector"] or "",
        },
        "preview": preview,
        "item_count": len(items),
    }
