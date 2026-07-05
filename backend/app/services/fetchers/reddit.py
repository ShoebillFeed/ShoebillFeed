import logging
from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher, socket_timeout

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_API_BASE = "https://oauth.reddit.com"


def _get_token(client_id: str, client_secret: str, username: str, password: str, user_agent: str) -> str:
    """Exchange credentials for a bearer token.

    Uses the 'password' grant when username+password are supplied (script app),
    otherwise falls back to 'client_credentials' (app-only, read-only).
    """
    if username and password:
        data = {"grant_type": "password", "username": username, "password": password}
    else:
        data = {"grant_type": "client_credentials"}

    resp = httpx.post(
        _TOKEN_URL,
        data=data,
        auth=(client_id, client_secret),
        headers={"User-Agent": user_agent},
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError(f"Reddit token response missing access_token: {resp.text[:200]}")
    return token


@register_fetcher("reddit")
class RedditFetcher(NewsFetcher):
    def fetch(self) -> list[RawNewsItem]:
        settings = get_settings()
        subreddit_name = self.config.get("subreddit", "")
        sort = self.config.get("sort", "hot")
        limit = int(self.config.get("limit", 25))

        if not subreddit_name:
            raise ValueError("Reddit source missing 'subreddit' in config")

        if not settings.reddit_client_id or not settings.reddit_client_secret:
            raise ValueError(
                "Reddit requires OAuth credentials. Set REDDIT_CLIENT_ID and "
                "REDDIT_CLIENT_SECRET in your .env (create an app at reddit.com/prefs/apps)."
            )

        try:
            token = _get_token(
                settings.reddit_client_id,
                settings.reddit_client_secret,
                settings.reddit_username,
                settings.reddit_password,
                settings.reddit_user_agent,
            )
        except Exception:
            logger.exception("Failed to obtain Reddit access token for r/%s", subreddit_name)
            return []

        url = f"{_API_BASE}/r/{subreddit_name}/{sort}"
        items: list[RawNewsItem] = []

        try:
            with socket_timeout(60):
                resp = httpx.get(
                    url,
                    params={"limit": limit, "raw_json": 1},
                    headers={
                        "Authorization": f"bearer {token}",
                        "User-Agent": settings.reddit_user_agent,
                    },
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
            logger.exception("Error fetching r/%s", subreddit_name)

        return items
