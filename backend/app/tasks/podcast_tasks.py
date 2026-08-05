import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.news_item import NewsItem
from app.models.news_cluster import NewsCluster
from app.models.podcast_show import PodcastShow
from app.models.podcast_episode import PodcastEpisode
from app.services.podcast_scheduling import due_shows
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.podcast_tasks.dispatch_due_podcasts", queue="podcast")
def dispatch_due_podcasts() -> int:
    """Beat task (every 15 min): scans active shows and dispatches generation
    for any show whose local schedule_time has just passed."""
    db = SessionLocal()
    try:
        shows = due_shows(db, datetime.now(timezone.utc))
        for show in shows:
            generate_podcast_episode.apply_async(args=[str(show.id)], queue="podcast")
        return len(shows)
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.podcast_tasks.generate_podcast_episode",
    queue="podcast",
    # Overrides the global 900s task_time_limit. A first-run Piper voice model
    # download plus CPU TTS synthesis for up to a 15-minute episode already
    # eats into the default; on top of that, Ollama's own request timeout for
    # the script call now scales with requested output size (see
    # ollama_provider.py::_timeout_for) and can itself run up to ~27 minutes
    # worst-case (8192 tokens at a conservative slow-CPU estimate) for a
    # max-length episode, so the task limit needs real headroom above that,
    # not just above the TTS side.
    soft_time_limit=2700,
    time_limit=3000,
)
def generate_podcast_episode(show_id: str) -> str:
    settings = get_settings()
    db = SessionLocal()
    try:
        show = db.scalar(select(PodcastShow).where(PodcastShow.id == uuid.UUID(show_id)))
        if not show:
            logger.warning("generate_podcast_episode: show %s not found", show_id)
            return "show not found"

        episode = PodcastEpisode(show_id=show.id, user_id=show.user_id, status="generating")
        db.add(episode)
        db.commit()
        db.refresh(episode)

        try:
            from app.services.podcast_script import (
                select_episode_items, build_script, story_payloads, build_episode_records,
            )
            from app.services.tts.factory import get_tts_provider
            from app.services.tts.audio_assembly import assemble_episode

            items = select_episode_items(db, show)
            if not items:
                raise ValueError("No news items matched this show's filters in the selected time window")

            script = build_script(show, items)
            if not script.turns:
                raise ValueError("LLM returned an empty podcast script")
            stories = story_payloads(items)

            tts = get_tts_provider()
            work_dir = os.path.join(settings.podcast_audio_dir, "_tmp", str(episode.id))
            os.makedirs(work_dir, exist_ok=True)

            turn_paths: list[str] = []
            turn_durations: list[float] = []
            turns_with_durations: list[tuple] = []
            for i, turn in enumerate(script.turns):
                host = next((h for h in show.hosts if h["id"] == turn.host_id), None)
                if not host:
                    continue
                out_path = os.path.join(work_dir, f"turn_{i}.wav")
                result = tts.synthesize(turn.text, host["voice"], out_path, speech_rate=show.speech_rate)
                turn_paths.append(result.audio_path)
                turn_durations.append(result.duration_seconds)
                turns_with_durations.append((turn, host, result.duration_seconds))

            if not turn_paths:
                raise ValueError("No audio turns were synthesized")

            final_rel_path = f"{show.user_id}/{episode.id}.mp3"
            final_abs_path = os.path.join(settings.podcast_audio_dir, final_rel_path)
            assembled = assemble_episode(turn_paths, turn_durations, final_abs_path)

            script_entries, shownotes = build_episode_records(turns_with_durations, stories)
            episode.script = script_entries
            episode.shownotes = shownotes or None
            episode.news_item_ids = [i.id for i in items if isinstance(i, NewsItem)]
            episode.news_cluster_ids = [i.id for i in items if isinstance(i, NewsCluster)]
            episode.audio_path = final_rel_path
            episode.duration_seconds = int(assembled.duration_seconds)
            episode.status = "ready"
            episode.generated_at = datetime.now(timezone.utc)

            for path in turn_paths:
                if os.path.exists(path):
                    os.remove(path)
            if os.path.isdir(work_dir):
                os.rmdir(work_dir)
        except Exception as exc:
            episode.status = "failed"
            episode.error_message = str(exc)[:2000]
            episode.generated_at = datetime.now(timezone.utc)
            logger.exception("Podcast episode generation failed for show %s", show_id)

        db.commit()
        return str(episode.id)
    finally:
        db.close()


@celery_app.task(name="app.tasks.podcast_tasks.cleanup_old_podcast_episodes", queue="default")
def cleanup_old_podcast_episodes(days: int = 30) -> int:
    settings = get_settings()
    db = SessionLocal()
    try:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
        old = db.scalars(select(PodcastEpisode).where(PodcastEpisode.created_at < cutoff)).all()
        count = len(old)
        for ep in old:
            if ep.audio_path:
                path = os.path.join(settings.podcast_audio_dir, ep.audio_path)
                if os.path.exists(path):
                    os.remove(path)
            db.delete(ep)
        db.commit()
        logger.info("Cleaned up %d old podcast episodes", count)
        return count
    except Exception:
        db.rollback()
        logger.exception("cleanup_old_podcast_episodes failed")
        raise
    finally:
        db.close()
