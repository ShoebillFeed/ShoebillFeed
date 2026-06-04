import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)


@register_fetcher("github")
class GitHubFetcher(NewsFetcher):
    """Fetches GitHub Releases or Trending repositories.

    Config keys (shared):
      mode      - "releases" | "trending" (default: releases)

    Releases mode:
      repo      - "owner/repo", e.g. "openai/openai-python"
      limit     - max releases to return (default: 20)
      token     - optional personal access token for higher rate limits
      prerelease - include pre-releases (default: false)

    Trending mode:
      language  - filter by language, e.g. "python" (default: all)
      since     - "daily" | "weekly" | "monthly" (default: daily)
    """

    def fetch(self) -> list[RawNewsItem]:
        mode = self.config.get("mode", "releases")
        if mode == "releases":
            return self._fetch_releases()
        elif mode == "trending":
            return self._fetch_trending()
        else:
            raise ValueError(f"Unknown GitHub mode: {mode!r}. Use 'releases' or 'trending'.")

    def _fetch_releases(self) -> list[RawNewsItem]:
        repo = self.config.get("repo", "").strip()
        limit = min(int(self.config.get("limit", 20)), 100)
        token = self.config.get("token", "").strip()
        include_prerelease = str(self.config.get("prerelease", "false")).lower() == "true"

        if not repo:
            raise ValueError("GitHub releases source missing 'repo' (e.g. 'openai/openai-python')")

        headers = {"User-Agent": "ShoebillFeed/1.0", "Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = httpx.get(
            f"https://api.github.com/repos/{repo}/releases",
            params={"per_page": limit},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()

        items: list[RawNewsItem] = []
        for release in resp.json():
            if release.get("draft"):
                continue
            if release.get("prerelease") and not include_prerelease:
                continue

            title = release.get("name") or release.get("tag_name", "")
            url = release.get("html_url", "")
            body = release.get("body") or ""
            published_str = release.get("published_at", "")

            if not title or not url:
                continue

            published_at = None
            if published_str:
                try:
                    published_at = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    ).astimezone(timezone.utc)
                except Exception:
                    pass

            items.append(RawNewsItem(
                title=f"{repo}: {title}",
                url=url,
                raw_content=body,
                published_at=published_at,
            ))

        return items

    def _fetch_trending(self) -> list[RawNewsItem]:
        language = self.config.get("language", "").strip()
        since = self.config.get("since", "daily")

        path = f"/trending/{language}" if language else "/trending"
        url = f"https://github.com{path}"

        resp = httpx.get(
            url,
            params={"since": since},
            headers={"User-Agent": "Mozilla/5.0 (compatible; ShoebillFeed/1.0)"},
            timeout=15,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        items: list[RawNewsItem] = []

        for article in soup.select("article.Box-row"):
            try:
                h2 = article.find("h2")
                if not h2:
                    continue
                link_tag = h2.find("a")
                if not link_tag:
                    continue
                href = link_tag.get("href", "").strip()
                if not href:
                    continue

                repo_name = href.strip("/").replace("/", " / ")
                repo_url = urljoin("https://github.com", href)

                desc_tag = article.find("p")
                description = desc_tag.get_text(strip=True) if desc_tag else ""

                items.append(RawNewsItem(
                    title=repo_name,
                    url=repo_url,
                    raw_content=description or repo_name,
                    published_at=datetime.now(timezone.utc),
                ))
            except Exception:
                logger.exception("Error parsing GitHub trending article")

        return items
