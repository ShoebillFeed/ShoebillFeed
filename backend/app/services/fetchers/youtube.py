import logging
from datetime import datetime, timezone

from googleapiclient.discovery import build

from app.config import get_settings
from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)


@register_fetcher("youtube")
class YouTubeFetcher(NewsFetcher):
    def fetch(self) -> list[RawNewsItem]:
        settings = get_settings()
        channel_id = self.config.get("channel_id", "")
        max_results = int(self.config.get("max_results", 10))

        if not channel_id:
            raise ValueError("YouTube source missing 'channel_id' in config")
        if not settings.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY not configured")

        youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
        items: list[RawNewsItem] = []

        try:
            response = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=max_results,
                order="date",
                type="video",
            ).execute()

            for item in response.get("items", []):
                snippet = item["snippet"]
                video_id = item["id"]["videoId"]
                published_at = datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                )
                content = f"{snippet['title']}\n\n{snippet.get('description', '')}"
                items.append(RawNewsItem(
                    title=snippet["title"],
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    raw_content=content,
                    published_at=published_at,
                ))
        except Exception:
            logger.exception("Error fetching YouTube channel %s", channel_id)
        finally:
            youtube.close()

        return items
