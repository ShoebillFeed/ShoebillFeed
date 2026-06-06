import logging
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)


@register_fetcher("scraper")
class WebScraperFetcher(NewsFetcher):
    """Generic CSS-selector-based web scraper for sites without feeds.

    Config keys:
      url               - page URL to scrape
      item_selector     - CSS selector matching each article/item container
      title_selector    - CSS selector for title within each item (default: h1,h2,h3)
      link_selector     - CSS selector for the link element within each item (default: a)
      content_selector  - optional CSS selector for content/description
      base_url          - base URL for resolving relative links (defaults to url)
    """

    def fetch(self) -> list[RawNewsItem]:
        url = self.config.get("url", "").strip()
        item_selector = self.config.get("item_selector", "").strip()
        title_selector = self.config.get("title_selector", "h1,h2,h3").strip()
        link_selector = self.config.get("link_selector", "a").strip()
        content_selector = self.config.get("content_selector", "").strip()
        base_url = self.config.get("base_url", url).strip() or url

        if not url:
            raise ValueError("Web scraper source missing 'url'")
        if not item_selector:
            raise ValueError("Web scraper source missing 'item_selector'")

        try:
            resp = httpx.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ShoebillFeed/1.0)"},
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("Error fetching scraper URL %s", url)
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items: list[RawNewsItem] = []

        for element in soup.select(item_selector):
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
