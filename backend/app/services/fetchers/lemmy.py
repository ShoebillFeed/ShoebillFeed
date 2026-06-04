import logging
from datetime import datetime, timezone

import httpx

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)


@register_fetcher("lemmy")
class LemmyFetcher(NewsFetcher):
    """Fetches posts from a Lemmy community via the public v3 JSON API.

    Config keys:
      instance_url  - e.g. "lemmy.world" or "https://lemmy.world"
      community     - community name, e.g. "technology"
      sort          - Hot | New | TopDay | TopWeek (default: Hot)
      limit         - max posts to fetch (default: 25)
    """

    def fetch(self) -> list[RawNewsItem]:
        instance = self.config.get("instance_url", "").rstrip("/")
        if instance and not instance.startswith(("http://", "https://")):
            instance = "https://" + instance
        community = self.config.get("community", "").strip()
        sort = self.config.get("sort", "Hot")
        limit = int(self.config.get("limit", 25))

        if not instance:
            raise ValueError("Lemmy source missing 'instance_url'")
        if not community:
            raise ValueError("Lemmy source missing 'community'")

        resp = httpx.get(
            f"{instance}/api/v3/post/list",
            params={"community_name": community, "sort": sort, "limit": limit, "type_": "Local"},
            headers={"User-Agent": "ShoebillFeed/1.0"},
            timeout=15,
        )
        resp.raise_for_status()

        items: list[RawNewsItem] = []
        for item in resp.json().get("posts", []):
            try:
                post = item.get("post", {})
                title = post.get("name", "").strip()
                if not title:
                    continue

                post_url = post.get("ap_id") or f"{instance}/post/{post.get('id', '')}"
                content = post.get("body") or post.get("url") or title

                published_at = None
                raw_date = post.get("published", "")
                if raw_date:
                    try:
                        published_at = datetime.fromisoformat(
                            raw_date.replace("Z", "+00:00")
                        ).astimezone(timezone.utc)
                    except Exception:
                        pass

                items.append(RawNewsItem(
                    title=title,
                    url=post_url,
                    raw_content=content,
                    published_at=published_at,
                ))
            except Exception:
                logger.exception("Error parsing Lemmy post")

        return items
