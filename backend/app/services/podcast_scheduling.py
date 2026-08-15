import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.podcast_show import PodcastShow
from app.models.podcast_episode import PodcastEpisode

logger = logging.getLogger(__name__)

DISPATCH_WINDOW_MINUTES = 15


def due_shows(db: Session, now_utc: datetime) -> list[PodcastShow]:
    """Active shows whose local schedule_time falls within the current
    dispatch window and that have not already produced an episode today.

    Beat entries are static/global, so the per-user timezone variability
    lives here rather than in the Celery schedule itself: this is called
    on a frequent fixed-UTC tick and decides per-show whether it's due.
    """
    shows = db.scalars(select(PodcastShow).where(PodcastShow.is_active == True)).all()  # noqa: E712
    due: list[PodcastShow] = []
    for show in shows:
        try:
            tz = ZoneInfo(show.timezone)
        except Exception:
            logger.warning("Podcast show %s has invalid timezone %r, skipping", show.id, show.timezone)
            continue

        local_now = now_utc.astimezone(tz)
        try:
            sched_h, sched_m = (int(x) for x in show.schedule_time.split(":"))
        except (ValueError, AttributeError):
            logger.warning("Podcast show %s has invalid schedule_time %r, skipping", show.id, show.schedule_time)
            continue

        scheduled_today_local = local_now.replace(hour=sched_h, minute=sched_m, second=0, microsecond=0)
        window_end = scheduled_today_local + timedelta(minutes=DISPATCH_WINDOW_MINUTES)
        if not (scheduled_today_local <= local_now < window_end):
            continue

        scheduled_today_utc = scheduled_today_local.astimezone(timezone.utc)
        exists_today = db.scalar(
            select(PodcastEpisode.id).where(
                PodcastEpisode.show_id == show.id,
                PodcastEpisode.created_at >= scheduled_today_utc,
            ).limit(1)
        )
        if exists_today:
            continue

        due.append(show)
    return due
