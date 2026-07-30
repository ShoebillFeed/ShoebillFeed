import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.config import get_settings
from app.models.user import User
from app.models.podcast_show import PodcastShow
from app.models.podcast_episode import PodcastEpisode
from app.schemas.podcast import (
    PodcastShowCreate,
    PodcastShowUpdate,
    PodcastShowOut,
    PodcastEpisodeOut,
    VoiceOut,
)
from app.schemas.pagination import Page
from app.services.range_streaming import range_response

router = APIRouter()


def _get_show(show_id: uuid.UUID, db: Session, user: User) -> PodcastShow:
    show = db.scalar(select(PodcastShow).where(PodcastShow.id == show_id, PodcastShow.user_id == user.id))
    if not show:
        raise HTTPException(status_code=404, detail="Podcast show not found")
    return show


def _get_episode(episode_id: uuid.UUID, db: Session, user: User) -> PodcastEpisode:
    episode = db.scalar(
        select(PodcastEpisode).where(PodcastEpisode.id == episode_id, PodcastEpisode.user_id == user.id)
    )
    if not episode:
        raise HTTPException(status_code=404, detail="Podcast episode not found")
    return episode


def _episode_out(episode: PodcastEpisode, show_name: str) -> PodcastEpisodeOut:
    out = PodcastEpisodeOut.model_validate(episode)
    out.show_name = show_name
    return out


def _delete_episode_audio(episode: PodcastEpisode) -> None:
    if not episode.audio_path:
        return
    settings = get_settings()
    path = os.path.join(settings.podcast_audio_dir, episode.audio_path)
    if os.path.exists(path):
        os.remove(path)


@router.get("/shows", response_model=list[PodcastShowOut])
def list_shows(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.scalars(
        select(PodcastShow).where(PodcastShow.user_id == current_user.id).order_by(PodcastShow.created_at)
    ).all()


@router.post("/shows", response_model=PodcastShowOut, status_code=201)
def create_show(payload: PodcastShowCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = PodcastShow(**payload.model_dump(), user_id=current_user.id)
    db.add(show)
    db.commit()
    db.refresh(show)
    return show


@router.get("/shows/{show_id}", response_model=PodcastShowOut)
def get_show(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_show(show_id, db, current_user)


@router.patch("/shows/{show_id}", response_model=PodcastShowOut)
def update_show(
    show_id: uuid.UUID,
    payload: PodcastShowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    show = _get_show(show_id, db, current_user)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(show, field, value)
    db.commit()
    db.refresh(show)
    return show


@router.delete("/shows/{show_id}", status_code=204)
def delete_show(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = _get_show(show_id, db, current_user)
    for episode in db.scalars(select(PodcastEpisode).where(PodcastEpisode.show_id == show.id)).all():
        _delete_episode_audio(episode)
    db.delete(show)  # cascades to episode rows via ondelete=CASCADE
    db.commit()


@router.post("/shows/{show_id}/generate")
def generate_now(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_show(show_id, db, current_user)
    from app.tasks.podcast_tasks import generate_podcast_episode
    generate_podcast_episode.apply_async(args=[str(show_id)], queue="podcast")
    return {"queued": True}


@router.get("/shows/{show_id}/episodes", response_model=list[PodcastEpisodeOut])
def list_show_episodes(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = _get_show(show_id, db, current_user)
    episodes = db.scalars(
        select(PodcastEpisode).where(PodcastEpisode.show_id == show.id).order_by(PodcastEpisode.created_at.desc())
    ).all()
    return [_episode_out(e, show.name) for e in episodes]


@router.get("/episodes", response_model=Page[PodcastEpisodeOut])
def list_episodes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import math

    base = select(PodcastEpisode).where(PodcastEpisode.user_id == current_user.id)
    all_episodes = db.scalars(base.order_by(PodcastEpisode.created_at.desc())).all()
    total = len(all_episodes)
    page_episodes = all_episodes[(page - 1) * page_size: page * page_size]

    show_ids = {e.show_id for e in page_episodes}
    show_names: dict[uuid.UUID, str] = {}
    if show_ids:
        rows = db.execute(select(PodcastShow.id, PodcastShow.name).where(PodcastShow.id.in_(show_ids)))
        show_names = {row.id: row.name for row in rows}

    items = [_episode_out(e, show_names.get(e.show_id, "")) for e in page_episodes]
    return Page(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 1,
    )


@router.get("/episodes/{episode_id}", response_model=PodcastEpisodeOut)
def get_episode(episode_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    episode = _get_episode(episode_id, db, current_user)
    show = db.scalar(select(PodcastShow).where(PodcastShow.id == episode.show_id))
    return _episode_out(episode, show.name if show else "")


@router.delete("/episodes/{episode_id}", status_code=204)
def delete_episode(episode_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    episode = _get_episode(episode_id, db, current_user)
    _delete_episode_audio(episode)
    db.delete(episode)
    db.commit()


@router.get("/episodes/{episode_id}/audio")
def stream_episode_audio(
    episode_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    episode = _get_episode(episode_id, db, current_user)
    if episode.status != "ready" or not episode.audio_path:
        raise HTTPException(status_code=404, detail="Episode audio not available")
    settings = get_settings()
    full_path = os.path.join(settings.podcast_audio_dir, episode.audio_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Episode audio file missing")
    return range_response(request, full_path, media_type="audio/mpeg")


@router.get("/voices", response_model=list[VoiceOut])
def list_voices(language: str = Query(...), _: User = Depends(get_current_user)):
    from app.services.tts.factory import get_tts_provider
    voices = get_tts_provider().list_voices(language)
    return [VoiceOut(id=v.id, label=v.label) for v in voices]
