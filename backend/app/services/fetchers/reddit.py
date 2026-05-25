import logging
from datetime import datetime, timezone

import httpx
import praw

from app.config import get_settings
from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)


@register_fetcher("reddit")
class RedditFetcher(NewsFetcher):
    def fetch(self) -> list[RawNewsItem]:
        settings = get_settings()
        subreddit_name = self.config.get("subreddit", "")
        sort = self.config.get("sort", "hot")
        limit = int(self.config.get("limit", 25))

        if not subreddit_name:
            raise ValueError("Reddit source missing 'subreddit' in config")

        if settings.reddit_client_id and settings.reddit_client_secret:
            return self._fetch_via_praw(settings, subreddit_name, sort, limit)
        else:
            logger.debug("Reddit credentials not configured, using public JSON API for r/%s", subreddit_name)
            return self._fetch_via_json(settings.reddit_user_agent, subreddit_name, sort, limit)

    def _fetch_via_praw(self, settings, subreddit_name: str, sort: str, limit: int) -> list[RawNewsItem]:
        kwargs: dict = {
            "client_id": settings.reddit_client_id,
            "client_secret": settings.reddit_client_secret,
            "user_agent": settings.reddit_user_agent,
        }
        if settings.reddit_username and settings.reddit_password:
            kwargs["username"] = settings.reddit_username
            kwargs["password"] = settings.reddit_password

        reddit = praw.Reddit(**kwargs)
        subreddit = reddit.subreddit(subreddit_name)
        items: list[RawNewsItem] = []

        try:
            listing = getattr(subreddit, sort)(limit=limit)
            for submission in listing:
                content = submission.selftext or submission.title
                items.append(RawNewsItem(
                    title=submission.title,
                    url=f"https://www.reddit.com{submission.permalink}",
                    raw_content=content,
                    published_at=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
                ))
        except Exception:
            logger.exception("Error fetching r/%s via PRAW", subreddit_name)

        return items

    def _fetch_via_json(self, user_agent: str, subreddit_name: str, sort: str, limit: int) -> list[RawNewsItem]:
        url = f"https://www.reddit.com/r/{subreddit_name}/{sort}.json"
        items: list[RawNewsItem] = []

        try:
            resp = httpx.get(
                url,
                params={"limit": limit, "raw_json": 1},
                headers={"User-Agent": user_agent},
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
            children = resp.json().get("data", {}).get("children", [])
            for child in children:
                post = child.get("data", {})
                title = post.get("title", "").strip()
                permalink = post.get("permalink", "")
                if not title or not permalink:
                    continue
                content = post.get("selftext") or title
                created_utc = post.get("created_utc")
                published_at = (
                    datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc else None
                )
                items.append(RawNewsItem(
                    title=title,
                    url=f"https://www.reddit.com{permalink}",
                    raw_content=content,
                    published_at=published_at,
                ))
        except Exception:
            logger.exception("Error fetching r/%s via public JSON API", subreddit_name)

        return items
