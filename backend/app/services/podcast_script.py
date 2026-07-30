from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.news_item import NewsItem
from app.models.news_cluster import NewsCluster
from app.models.podcast_show import PodcastShow
from app.services.feed_ranking import build_feed
from app.services.llm.factory import get_llm_provider
from app.services.llm.base import PodcastScriptResult

_WORDS_PER_MINUTE = 150
_INTRO_OUTRO_WORDS = 120
_BASE_WORDS_PER_STORY = 130
_EXTRA_WORDS_PER_HOST = 15
_MAX_STORIES = 15


def estimate_story_count(target_minutes: int, host_count: int) -> int:
    total_words = target_minutes * _WORDS_PER_MINUTE
    per_story_words = _BASE_WORDS_PER_STORY + (host_count - 1) * _EXTRA_WORDS_PER_HOST
    n = (total_words - _INTRO_OUTRO_WORDS) // per_story_words
    return int(min(max(1, n), _MAX_STORIES))


def _entry_dt(entry) -> datetime | None:
    if isinstance(entry, NewsItem):
        dt = entry.published_at or entry.fetched_at
    else:
        dt = entry.published_at or entry.created_at
    if dt and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def select_episode_items(db: Session, show: PodcastShow) -> list[NewsItem | NewsCluster]:
    entries = build_feed(
        db, tab="relevant", user_id=show.user_id,
        category_ids=show.category_ids, source_ids=show.source_ids,
        is_read=None, read_later=None,
    )
    cutoff = datetime.now(timezone.utc) - timedelta(hours=show.time_window_hours)
    entries = [e for e in entries if (dt := _entry_dt(e)) and dt >= cutoff]
    n = estimate_story_count(show.target_length_minutes, len(show.hosts))
    return entries[:n]


def _story_payload(entry: NewsItem | NewsCluster) -> dict:
    if isinstance(entry, NewsItem):
        return {
            "title": entry.title,
            "content": entry.abstract or entry.raw_content or entry.title,
            "source_name": entry.source.name if entry.source else "Unknown source",
        }
    source_names = sorted({item.source.name for item in entry.items if item.source})
    return {
        "title": entry.title or "Untitled",
        "content": entry.unified_abstract or entry.title or "",
        "source_name": ", ".join(source_names) if source_names else "Multiple sources",
    }


def build_script(show: PodcastShow, items: list[NewsItem | NewsCluster]) -> PodcastScriptResult:
    hosts = [
        {"id": h["id"], "name": h["name"], "character_prompt": h["character_prompt"]}
        for h in show.hosts
    ]
    stories = [_story_payload(entry) for entry in items]
    provider = get_llm_provider()
    return provider.generate_podcast_script(
        hosts=hosts,
        stories=stories,
        target_minutes=show.target_length_minutes,
        language=show.language,
    )
