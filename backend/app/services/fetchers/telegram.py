import logging
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)


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
            resp = httpx.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ShoebillFeed/1.0)"},
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("Error fetching Telegram channel %s", channel)
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items: list[RawNewsItem] = []

        for wrap in soup.select(".tgme_widget_message_wrap"):
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
