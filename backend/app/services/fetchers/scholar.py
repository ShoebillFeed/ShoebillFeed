import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser
from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher, socket_timeout

logger = logging.getLogger(__name__)

_ARXIV_URL = "https://export.arxiv.org/api/query?search_query=all:{query}&max_results=20&sortBy=submittedDate&sortOrder=descending"


@register_fetcher("arxiv")
@register_fetcher("scholar")  # keep for backward-compat with existing DB records
class ScholarFetcher(NewsFetcher):
    """Fetches academic papers from arXiv via the official Atom API.

    Config keys:
      query  - search keywords (required)
    """

    def fetch(self) -> list[RawNewsItem]:
        query = self.config.get("query", "").strip()
        if not query:
            raise ValueError("Scholar source missing 'query' in config")

        url_template = _ARXIV_URL

        url = url_template.format(query=quote_plus(query))
        logger.debug("Fetching arXiv Atom feed: %s", url)

        with socket_timeout(30):
            feed = feedparser.parse(url, request_headers={"User-Agent": "ShoebillFeed/1.0 (academic RSS reader)"})
        status = feed.get("status")
        logger.debug("arXiv feed status=%s bozo=%s entries=%d", status, feed.get("bozo"), len(feed.entries))
        if status == 429:
            raise ValueError(f"arXiv rate-limited (429) for query {query!r} — will retry")
        if status and status >= 400:
            raise ValueError(f"arXiv returned HTTP {status} for query {query!r}")
        if feed.get("bozo") and not feed.entries:
            logger.warning("arXiv feed returned no entries (bozo_exception=%s) — skipping", feed.get("bozo_exception"))
            return []

        items: list[RawNewsItem] = []
        for entry in feed.entries:
            try:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue

                content = self._extract_content(entry)
                published_at = self._parse_date(entry)

                items.append(RawNewsItem(
                    title=title,
                    url=link,
                    raw_content=content,
                    published_at=published_at,
                    image_url=None,
                ))
            except Exception:
                logger.exception("Error parsing scholar entry %s", entry.get("link"))

        return items

    def _extract_content(self, entry) -> str:
        for key in ("content", "summary_detail", "summary"):
            val = entry.get(key)
            if val:
                if isinstance(val, list):
                    val = val[0]
                html = val.get("value", "") if isinstance(val, dict) else str(val)
                if html:
                    return BeautifulSoup(html, "lxml").get_text(separator=" ", strip=True)
        return ""

    def _parse_date(self, entry) -> datetime | None:
        for key in ("published", "updated"):
            val = entry.get(key)
            if val:
                try:
                    return parsedate_to_datetime(val).astimezone(timezone.utc)
                except Exception:
                    pass
        struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if struct:
            return datetime(*struct[:6], tzinfo=timezone.utc)
        return None
