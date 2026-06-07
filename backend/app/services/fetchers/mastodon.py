import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher, socket_timeout

logger = logging.getLogger(__name__)


@register_fetcher("mastodon")
class MastodonFetcher(NewsFetcher):
    """Fetches public Mastodon timelines via built-in RSS feeds.

    Config keys:
      instance_url  - e.g. "https://mastodon.social"
      feed_type     - "user" | "hashtag" | "local" (default: "hashtag")
      name          - username (without @) for feed_type=user, hashtag for feed_type=hashtag
    """

    def fetch(self) -> list[RawNewsItem]:
        instance = self.config.get("instance_url", "").rstrip("/")
        if instance and not instance.startswith(("http://", "https://")):
            instance = "https://" + instance
        feed_type = self.config.get("feed_type", "hashtag")
        name = self.config.get("name", "")

        if not instance:
            raise ValueError("Mastodon source missing 'instance_url' in config")

        if feed_type == "user":
            if not name:
                raise ValueError("Mastodon 'user' feed requires 'name' (username)")
            url = f"{instance}/@{name}.rss"
        elif feed_type == "hashtag":
            if not name:
                raise ValueError("Mastodon 'hashtag' feed requires 'name' (hashtag)")
            tag = name.lstrip("#")
            url = f"{instance}/tags/{tag}.rss"
        elif feed_type == "local":
            url = f"{instance}/public/local.rss"
        else:
            raise ValueError(f"Unknown Mastodon feed_type: {feed_type!r}. Use 'user', 'hashtag', or 'local'.")

        logger.debug("Fetching Mastodon RSS from %s", url)
        with socket_timeout(30):
            feed = feedparser.parse(url)
        if feed.get("bozo") and not feed.entries:
            raise ValueError(f"Could not parse Mastodon RSS feed at {url!r}")

        items: list[RawNewsItem] = []
        for entry in feed.entries:
            try:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not link:
                    continue

                content = self._extract_content(entry)
                if not title:
                    title = content[:80] + "…" if len(content) > 80 else content

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
                logger.exception("Error parsing Mastodon entry %s", entry.get("link"))

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

    def _extract_image(self, entry) -> str | None:
        for mc in entry.get("media_content") or []:
            if mc.get("medium") == "image" or mc.get("type", "").startswith("image/"):
                url = mc.get("url", "")
                if url:
                    return url
        for enc in entry.get("enclosures") or []:
            if enc.get("type", "").startswith("image/"):
                return enc.get("href") or enc.get("url")
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
