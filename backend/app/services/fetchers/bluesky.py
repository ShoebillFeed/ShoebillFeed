import logging
from datetime import datetime, timezone

import httpx

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)

_BASE = "https://public.api.bsky.app/xrpc"


@register_fetcher("bluesky")
class BlueskyFetcher(NewsFetcher):
    """Fetches posts from Bluesky via the public AT Protocol AppView API.

    Config keys:
      feed_type  - "user" | "search" (default: user)
      handle     - Bluesky handle for feed_type=user, e.g. "bsky.app"
      query      - search query / hashtag for feed_type=search, e.g. "#AI"
      limit      - max posts (default: 20)
    """

    def fetch(self) -> list[RawNewsItem]:
        feed_type = self.config.get("feed_type", "user")
        limit = min(int(self.config.get("limit", 20)), 100)

        if feed_type == "user":
            handle = self.config.get("handle", "").strip().lstrip("@")
            if not handle:
                raise ValueError("Bluesky 'user' feed requires 'handle'")
            return self._fetch_user(handle, limit)
        elif feed_type == "search":
            query = self.config.get("query", "").strip()
            if not query:
                raise ValueError("Bluesky 'search' feed requires 'query'")
            return self._fetch_search(query, limit)
        else:
            raise ValueError(f"Unknown Bluesky feed_type: {feed_type!r}. Use 'user' or 'search'.")

    def _post_to_item(self, post: dict) -> RawNewsItem | None:
        record = post.get("record", {})
        text = record.get("text", "").strip()
        if not text:
            return None

        uri = post.get("uri", "")  # at://did/app.bsky.feed.post/rkey
        author = post.get("author", {})
        handle = author.get("handle", "")
        rkey = uri.rsplit("/", 1)[-1] if uri else ""
        if not handle or not rkey:
            return None

        url = f"https://bsky.app/profile/{handle}/post/{rkey}"
        title = text[:100] + "…" if len(text) > 100 else text

        published_at = None
        raw_date = record.get("createdAt", "")
        if raw_date:
            try:
                published_at = datetime.fromisoformat(
                    raw_date.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except Exception:
                pass

        image_url = None
        embed = post.get("embed", {})
        if embed.get("$type") == "app.bsky.embed.images#view":
            images = embed.get("images", [])
            if images:
                image_url = images[0].get("fullsize") or images[0].get("thumb")

        return RawNewsItem(title=title, url=url, raw_content=text, published_at=published_at, image_url=image_url)

    def _fetch_user(self, handle: str, limit: int) -> list[RawNewsItem]:
        try:
            resp = httpx.get(
                f"{_BASE}/app.bsky.feed.getAuthorFeed",
                params={"actor": handle, "limit": limit},
                headers={"User-Agent": "ShoebillFeed/1.0"},
                timeout=15,
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("Error fetching Bluesky user feed for %s", handle)
            return []

        items: list[RawNewsItem] = []
        for feed_item in resp.json().get("feed", []):
            try:
                item = self._post_to_item(feed_item.get("post", {}))
                if item:
                    items.append(item)
            except Exception:
                logger.exception("Error parsing Bluesky post")
        return items

    def _fetch_search(self, query: str, limit: int) -> list[RawNewsItem]:
        try:
            resp = httpx.get(
                f"{_BASE}/app.bsky.feed.searchPosts",
                params={"q": query, "limit": limit},
                headers={"User-Agent": "ShoebillFeed/1.0"},
                timeout=15,
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("Error fetching Bluesky search for %s", query)
            return []

        items: list[RawNewsItem] = []
        for post in resp.json().get("posts", []):
            try:
                item = self._post_to_item(post)
                if item:
                    items.append(item)
            except Exception:
                logger.exception("Error parsing Bluesky post")
        return items
