import logging
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


@register_fetcher("telegram")
class TelegramFetcher(NewsFetcher):
    """Fetches messages from a public Telegram channel via the t.me/s/{channel} web view.

    Config keys:
      channel  - channel username without @, e.g. "bbcnews"
    """

    def fetch(self) -> list[RawNewsItem]:
        channel = self.config.get("channel", "").strip().lstrip("@")
        if not channel:
            raise ValueError("Telegram source missing 'channel'")

        url = f"https://t.me/s/{channel}"
        try:
            resp = httpx.get(url, headers=_HEADERS, timeout=20, follow_redirects=True)
            resp.raise_for_status()
        except Exception:
            logger.exception("Error fetching Telegram channel %s", channel)
            return []

        # If Telegram redirected away from /s/ the channel has no web preview
        if "/s/" not in str(resp.url):
            logger.warning(
                "Telegram channel %s has no public web preview (redirected to %s)",
                channel, resp.url,
            )
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        wraps = soup.select(".tgme_widget_message_wrap")
        logger.debug("Telegram %s: %d message wrappers found", channel, len(wraps))

        if not wraps:
            # Log a snippet so we can spot structural changes
            logger.warning(
                "Telegram %s: no messages found — page length %d, first 300 chars: %r",
                channel, len(resp.text), resp.text[:300],
            )
            return []

        items: list[RawNewsItem] = []
        for wrap in wraps:
            try:
                msg_div = wrap.select_one(".tgme_widget_message_text")
                text = msg_div.get_text(separator=" ", strip=True) if msg_div else ""
                if not text:
                    continue

                date_link = wrap.select_one("a.tgme_widget_message_date")
                msg_url = date_link.get("href", "") if date_link else ""
                if not msg_url:
                    continue

                published_at = None
                time_tag = wrap.select_one("time[datetime]")
                if time_tag:
                    try:
                        published_at = datetime.fromisoformat(
                            time_tag["datetime"]
                        ).astimezone(timezone.utc)
                    except Exception:
                        pass

                title = text[:100] + "…" if len(text) > 100 else text

                image_url = None
                photo_wrap = wrap.select_one(".tgme_widget_message_photo_wrap")
                if photo_wrap:
                    style = photo_wrap.get("style", "")
                    m = re.search(r"url\(['\"](.+?)['\"]\)", style)
                    if m:
                        image_url = m.group(1)

                items.append(RawNewsItem(
                    title=title,
                    url=msg_url,
                    raw_content=text,
                    published_at=published_at,
                    image_url=image_url,
                ))
            except Exception:
                logger.exception("Error parsing Telegram message")

        return items
