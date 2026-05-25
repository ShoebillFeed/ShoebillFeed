import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)


@register_fetcher("rss")
class RSSFetcher(NewsFetcher):
    def fetch(self) -> list[RawNewsItem]:
        url = self.config.get("url", "")
        if not url:
            raise ValueError("RSS source missing 'url' in config")

        feed = feedparser.parse(url)
        if feed.get("bozo") and not feed.entries:
            discovered = self._autodiscover_feed(url)
            if discovered:
                logger.info("Autodiscovered feed %s from %s", discovered, url)
                feed = feedparser.parse(discovered)
            else:
                raise ValueError(
                    f"{url!r} is not a valid RSS/Atom feed and no feed link was found on the page. "
                    f"Please set the source URL to the direct feed URL (e.g. https://www.heise.de/rss/heise-atom.xml)."
                )
        logger.debug("RSS feed %s returned %d entries (status=%s)", url, len(feed.entries), feed.get("status"))
        items: list[RawNewsItem] = []

        for entry in feed.entries:
            try:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue

                content = self._extract_content(entry, link)
                published_at = self._parse_date(entry)
                image_url = self._extract_image(entry)

                items.append(RawNewsItem(
                    title=title,
                    url=link,
                    raw_content=content,
                    published_at=published_at,
                    image_url=image_url,
                ))
            except Exception:
                logger.exception("Error parsing RSS entry %s", entry.get("link"))

        return items

    def _autodiscover_feed(self, url: str) -> str | None:
        try:
            resp = httpx.get(url, timeout=10, follow_redirects=True, headers={"User-Agent": "HarmonicPhoenix/1.0"})
            soup = BeautifulSoup(resp.text, "lxml")
            for link_tag in soup.find_all("link", rel="alternate"):
                if link_tag.get("type") in ("application/rss+xml", "application/atom+xml"):
                    href = link_tag.get("href", "").strip()
                    if href:
                        return urljoin(url, href)
        except Exception:
            logger.debug("Could not autodiscover feed for %s", url)
        return None

    def _extract_content(self, entry, link: str) -> str:
        for key in ("content", "summary_detail", "summary"):
            val = entry.get(key)
            if val:
                if isinstance(val, list):
                    val = val[0]
                text = val.get("value", "") if isinstance(val, dict) else str(val)
                if text:
                    return BeautifulSoup(text, "lxml").get_text(separator=" ", strip=True)

        try:
            resp = httpx.get(link, timeout=10, follow_redirects=True, headers={"User-Agent": "HarmonicPhoenix/1.0"})
            soup = BeautifulSoup(resp.text, "lxml")
            article = soup.find("article") or soup.find("main") or soup.body
            if article:
                return article.get_text(separator=" ", strip=True)[:8000]
        except Exception:
            logger.debug("Could not fetch full content for %s", link)

        return ""

    def _extract_image(self, entry) -> str | None:
        # media:thumbnail
        thumbnails = entry.get("media_thumbnail") or []
        if thumbnails:
            url = thumbnails[0].get("url", "")
            if url:
                return url

        # media:content with image medium or image/* type
        for mc in entry.get("media_content") or []:
            if mc.get("medium") == "image" or mc.get("type", "").startswith("image/"):
                url = mc.get("url", "")
                if url:
                    return url

        # enclosures
        for enc in entry.get("enclosures") or []:
            if enc.get("type", "").startswith("image/"):
                url = enc.get("href") or enc.get("url", "")
                if url:
                    return url

        # first <img> in content HTML
        for key in ("content", "summary_detail", "summary"):
            val = entry.get(key)
            if val:
                if isinstance(val, list):
                    val = val[0]
                html = val.get("value", "") if isinstance(val, dict) else str(val)
                if html:
                    soup = BeautifulSoup(html, "lxml")
                    img = soup.find("img")
                    if img:
                        src = img.get("src", "")
                        if src.startswith(("http://", "https://")):
                            return src

        return None

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
