import logging
import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; ShoebillFeed/1.0)"


class RobotsDisallowedError(Exception):
    """Raised when a site's robots.txt disallows fetching the given URL."""

# Values that are overwhelmingly session tokens rather than article identifiers:
# 16+ hex chars (MD5 halves, random hex) or standard UUIDs.
_SESSION_VALUE_RE = re.compile(
    r"^[a-f0-9]{16,}$"
    r"|^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


DEFAULT_TITLE_SELECTOR = "h1,h2,h3"
DEFAULT_LINK_SELECTOR = "a"
# If scraped excerpt is shorter than this, try fetching the full article page.
_MIN_CONTENT_LEN = 300


def _scrub_url(url: str) -> str:
    """Strip query params whose values look like random session tokens.

    Complements the known-name stripping in canonical_url() for sites that use
    non-standard session param names (e.g. ?token=a3f9..., ?k=uuid-here).
    Only applied in the scraper context where arbitrary site URLs are encountered.
    """
    parsed = urlparse(url)
    if not parsed.query:
        return url
    qs = parse_qs(parsed.query, keep_blank_values=True)
    clean = {
        k: v for k, v in qs.items()
        if not (len(v) == 1 and _SESSION_VALUE_RE.match(v[0]))
    }
    return urlunparse(parsed._replace(query=urlencode(sorted(clean.items()), doseq=True)))


def robots_allowed(url: str, timeout: float = 10) -> bool:
    """Check the host's robots.txt for permission to fetch `url`.

    Fails open (returns True) if robots.txt is missing or can't be fetched,
    since absence of a robots.txt means no restrictions apply.
    """
    parsed = urlparse(url)
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    parser = RobotFileParser()
    try:
        resp = httpx.get(
            robots_url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
        )
        if resp.status_code >= 400:
            return True
        parser.parse(resp.text.splitlines())
    except Exception:
        logger.warning("Could not fetch robots.txt at %s, allowing by default", robots_url)
        return True
    return parser.can_fetch(USER_AGENT, url)


def _extract_article_text(html: str) -> str:
    """Pull main body text from an article page — mirrors the RSS fetcher fallback."""
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("article") or soup.find("main") or soup.body
    if main:
        return main.get_text(separator=" ", strip=True)[:8000]
    return ""


def _fetch_full_article(url: str, allowed_netloc: str, timeout: float = 10) -> str:
    """Fetch the full article page and return its main text.

    Only follows URLs on the same netloc as the listing page — the domain's
    robots.txt was already checked when the listing page was fetched.
    Returns "" on any failure so the caller can fall back to the excerpt.
    """
    if urlparse(url).netloc != allowed_netloc:
        return ""
    try:
        resp = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return _extract_article_text(resp.text)
    except Exception:
        logger.debug("Could not fetch article content from %s", url)
        return ""


def fetch_html(url: str, timeout: float = 15) -> str:
    """Fetch a page's HTML. Raises on network/HTTP errors, or RobotsDisallowedError
    if the site's robots.txt disallows fetching this URL."""
    if not robots_allowed(url):
        raise RobotsDisallowedError(f"Scraping disallowed by robots.txt: {url}")

    resp = httpx.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    )
    resp.raise_for_status()
    return resp.text


def parse_scraper_items(
    html: str,
    base_url: str,
    item_selector: str,
    title_selector: str = DEFAULT_TITLE_SELECTOR,
    link_selector: str = DEFAULT_LINK_SELECTOR,
    content_selector: str | None = None,
) -> list[RawNewsItem]:
    """Extract items from HTML using the given CSS selectors. Returns [] on
    invalid selectors or if nothing matches, rather than raising."""
    soup = BeautifulSoup(html, "lxml")

    try:
        elements = soup.select(item_selector)
    except Exception:
        logger.exception("Invalid item_selector %r", item_selector)
        return []

    items: list[RawNewsItem] = []
    for element in elements:
        try:
            title_el = element.select_one(title_selector)
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            # Prefer explicit link selector; fall back to title element if it is an <a>
            link_el = element.select_one(link_selector)
            href = (link_el.get("href") or "").strip() if link_el else ""
            if not href and title_el.name == "a":
                href = (title_el.get("href") or "").strip()
            if not href:
                continue

            full_url = urljoin(base_url, href)
            if urlparse(full_url).scheme not in ("http", "https"):
                continue
            full_url = _scrub_url(full_url)

            content = ""
            if content_selector:
                content_el = element.select_one(content_selector)
                if content_el:
                    content = content_el.get_text(separator=" ", strip=True)
            if not content:
                content = element.get_text(separator=" ", strip=True)

            items.append(RawNewsItem(
                title=title,
                url=full_url,
                raw_content=content,
                published_at=None,
            ))
        except Exception:
            logger.exception("Error parsing scraped item")

    return items


@register_fetcher("scraper")
class WebScraperFetcher(NewsFetcher):
    """Generic CSS-selector-based web scraper for sites without feeds.

    Config keys:
      url                  - page URL to scrape
      item_selector        - CSS selector matching each article/item container
      title_selector       - CSS selector for title within each item (default: h1,h2,h3)
      link_selector        - CSS selector for the link element within each item (default: a)
      content_selector     - optional CSS selector for content/description
      base_url             - base URL for resolving relative links (defaults to url)
      fetch_full_articles  - follow article links to fetch full text when the listing
                             excerpt is < 300 chars (default: true). Set to false for
                             listing pages that already contain full content, or when
                             the target site blocks article-level requests.
    """

    def fetch(self) -> list[RawNewsItem]:
        url = self.config.get("url", "").strip()
        item_selector = self.config.get("item_selector", "").strip()
        title_selector = self.config.get("title_selector", DEFAULT_TITLE_SELECTOR).strip()
        link_selector = self.config.get("link_selector", DEFAULT_LINK_SELECTOR).strip()
        content_selector = self.config.get("content_selector", "").strip() or None
        base_url = self.config.get("base_url", url).strip() or url
        raw_ff = self.config.get("fetch_full_articles", True)
        fetch_full = raw_ff not in (False, "false", "0", 0)

        if not url:
            raise ValueError("Web scraper source missing 'url'")
        if not item_selector:
            raise ValueError("Web scraper source missing 'item_selector'")

        try:
            html = fetch_html(url)
        except RobotsDisallowedError:
            logger.warning("Skipping scraper source %s: disallowed by robots.txt", url)
            return []
        except Exception:
            logger.exception("Error fetching scraper URL %s", url)
            return []

        items = parse_scraper_items(html, base_url, item_selector, title_selector, link_selector, content_selector)

        if fetch_full:
            listing_netloc = urlparse(url).netloc
            for item in items:
                if len(item.raw_content) < _MIN_CONTENT_LEN:
                    full = _fetch_full_article(item.url, listing_netloc)
                    if full:
                        item.raw_content = full

        return items
