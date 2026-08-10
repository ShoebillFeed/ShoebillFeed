import os
import uuid

from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.config import get_settings
from app.limiter import limiter
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
from app.services.podcast_feed import generate_feed_token, render_rss_feed, episode_description
from app.services.range_streaming import range_response

router = APIRouter()

# Content-Type -> (file extension, Pillow format name).
_COVER_CONTENT_TYPES = {
    "image/png": ("png", "PNG"),
    "image/jpeg": ("jpg", "JPEG"),
    "image/webp": ("webp", "WEBP"),
}
_MAX_COVER_BYTES = 5 * 1024 * 1024
# 1400px matches Apple Podcasts' documented minimum artwork dimension, so
# public RSS feeds stay compliant -- well beyond what the in-app UI ever
# needs (a ~40-64px thumbnail), but uploads straight off a phone camera can
# be several times larger than this in each dimension, so it's still a real
# size reduction. thumbnail() only ever shrinks, never upscales a smaller image.
_COVER_MAX_DIMENSION = 1400


def _resize_cover_image(data: bytes, pillow_format: str) -> bytes:
    try:
        image = Image.open(BytesIO(data))
        image.load()
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")
    image.thumbnail((_COVER_MAX_DIMENSION, _COVER_MAX_DIMENSION), Image.LANCZOS)
    if pillow_format == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")  # JPEG has no alpha channel
    out = BytesIO()
    save_kwargs = {"optimize": True}
    if pillow_format in ("JPEG", "WEBP"):
        save_kwargs["quality"] = 85
    image.save(out, format=pillow_format, **save_kwargs)
    return out.getvalue()


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


def _get_show_by_feed_token(feed_token: str, db: Session) -> PodcastShow:
    show = db.scalar(
        select(PodcastShow).where(
            PodcastShow.public_feed_token == feed_token, PodcastShow.public_feed_enabled == True  # noqa: E712
        )
    )
    if not show:
        # 404, not 401/403 -- an invalid/guessed/disabled token should look
        # indistinguishable from a URL that never existed.
        raise HTTPException(status_code=404, detail="Podcast feed not found")
    return show


def _show_out(show: PodcastShow) -> PodcastShowOut:
    out = PodcastShowOut.model_validate(show)
    base = get_settings().public_base_url.rstrip("/")
    if show.public_feed_enabled and show.public_feed_token and base:
        out.public_feed_url = f"{base}/api/podcasts/public/{show.public_feed_token}/feed.xml"
    if show.cover_image_path:
        # Relative, same-origin path -- served through the authenticated
        # /shows/{id}/cover route below, so the browser's session cookie
        # covers it automatically, same as any other /api request.
        out.cover_image_url = f"/api/podcasts/shows/{show.id}/cover"
    return out


def _cover_abs_path(show: PodcastShow) -> str | None:
    if not show.cover_image_path:
        return None
    return os.path.join(get_settings().podcast_audio_dir, show.cover_image_path)


def _episode_out(episode: PodcastEpisode, show_name: str, cover_image_path: str | None = None) -> PodcastEpisodeOut:
    out = PodcastEpisodeOut.model_validate(episode)
    out.show_name = show_name
    if cover_image_path:
        out.show_cover_image_url = f"/api/podcasts/shows/{episode.show_id}/cover"
    out.description = episode_description(episode)
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
    shows = db.scalars(
        select(PodcastShow).where(PodcastShow.user_id == current_user.id).order_by(PodcastShow.created_at)
    ).all()
    return [_show_out(s) for s in shows]


@router.post("/shows", response_model=PodcastShowOut, status_code=201)
def create_show(payload: PodcastShowCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = PodcastShow(**payload.model_dump(), user_id=current_user.id)
    db.add(show)
    db.commit()
    db.refresh(show)
    return _show_out(show)


@router.get("/shows/{show_id}", response_model=PodcastShowOut)
def get_show(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _show_out(_get_show(show_id, db, current_user))


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
    return _show_out(show)


@router.post("/shows/{show_id}/public-feed", response_model=PodcastShowOut)
def enable_public_feed(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = _get_show(show_id, db, current_user)
    if not get_settings().public_base_url:
        raise HTTPException(status_code=400, detail="PUBLIC_BASE_URL is not configured on the server")
    if not show.public_feed_token:
        show.public_feed_token = generate_feed_token()
    show.public_feed_enabled = True
    db.commit()
    db.refresh(show)
    return _show_out(show)


@router.delete("/shows/{show_id}/public-feed", response_model=PodcastShowOut)
def disable_public_feed(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = _get_show(show_id, db, current_user)
    show.public_feed_enabled = False
    db.commit()
    db.refresh(show)
    return _show_out(show)


@router.post("/shows/{show_id}/public-feed/regenerate", response_model=PodcastShowOut)
def regenerate_public_feed(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = _get_show(show_id, db, current_user)
    if not show.public_feed_enabled:
        raise HTTPException(status_code=400, detail="Public feed is not enabled for this show")
    show.public_feed_token = generate_feed_token()
    db.commit()
    db.refresh(show)
    return _show_out(show)


@router.post("/shows/{show_id}/cover", response_model=PodcastShowOut)
async def upload_cover(
    show_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    show = _get_show(show_id, db, current_user)
    content_type_entry = _COVER_CONTENT_TYPES.get(file.content_type)
    if not content_type_entry:
        raise HTTPException(status_code=400, detail="Cover image must be PNG, JPEG, or WebP")
    ext, pillow_format = content_type_entry
    data = await file.read()
    if len(data) > _MAX_COVER_BYTES:
        raise HTTPException(status_code=400, detail="Cover image must be under 5MB")
    data = _resize_cover_image(data, pillow_format)

    settings = get_settings()
    covers_dir = os.path.join(settings.podcast_audio_dir, "covers")
    os.makedirs(covers_dir, exist_ok=True)

    old_path = _cover_abs_path(show)
    if old_path and os.path.exists(old_path):
        os.remove(old_path)

    rel_path = f"covers/{show.id}.{ext}"
    with open(os.path.join(settings.podcast_audio_dir, rel_path), "wb") as f:
        f.write(data)
    show.cover_image_path = rel_path
    db.commit()
    db.refresh(show)
    return _show_out(show)


@router.delete("/shows/{show_id}/cover", response_model=PodcastShowOut)
def delete_cover(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = _get_show(show_id, db, current_user)
    old_path = _cover_abs_path(show)
    if old_path and os.path.exists(old_path):
        os.remove(old_path)
    show.cover_image_path = None
    db.commit()
    db.refresh(show)
    return _show_out(show)


@router.get("/shows/{show_id}/cover")
def get_cover(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = _get_show(show_id, db, current_user)
    path = _cover_abs_path(show)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No cover image set")
    return FileResponse(path)


@router.delete("/shows/{show_id}", status_code=204)
def delete_show(show_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    show = _get_show(show_id, db, current_user)
    for episode in db.scalars(select(PodcastEpisode).where(PodcastEpisode.show_id == show.id)).all():
        _delete_episode_audio(episode)
    cover_path = _cover_abs_path(show)
    if cover_path and os.path.exists(cover_path):
        os.remove(cover_path)
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
    return [_episode_out(e, show.name, show.cover_image_path) for e in episodes]


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
    show_meta: dict[uuid.UUID, tuple[str, str | None]] = {}
    if show_ids:
        rows = db.execute(
            select(PodcastShow.id, PodcastShow.name, PodcastShow.cover_image_path).where(PodcastShow.id.in_(show_ids))
        )
        show_meta = {row.id: (row.name, row.cover_image_path) for row in rows}

    items = [_episode_out(e, *show_meta.get(e.show_id, ("", None))) for e in page_episodes]
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
    return _episode_out(episode, show.name if show else "", show.cover_image_path if show else None)


@router.delete("/episodes/{episode_id}", status_code=204)
def delete_episode(episode_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    episode = _get_episode(episode_id, db, current_user)
    _delete_episode_audio(episode)
    db.delete(episode)
    db.commit()


@router.post("/episodes/{episode_id}/regenerate")
def regenerate_episode(episode_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    episode = _get_episode(episode_id, db, current_user)
    if episode.status == "generating":
        raise HTTPException(status_code=409, detail="Episode is already generating")
    from app.tasks.podcast_tasks import regenerate_podcast_episode
    regenerate_podcast_episode.apply_async(args=[str(episode_id)], queue="podcast")
    return {"queued": True}


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


@router.get("/voices/preview")
def preview_voice(voice_id: str = Query(...), language: str = Query(...), _: User = Depends(get_current_user)):
    """Synthesize a short, fixed sample phrase for `voice_id` so the show
    form can play it before committing to it. Deliberately not persisted
    anywhere -- generated to a throwaway temp file and streamed back."""
    import tempfile

    from app.services.tts.factory import get_tts_provider
    from app.services.tts.preview_text import preview_phrase_for

    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        provider = get_tts_provider()
        provider.synthesize(preview_phrase_for(language), voice_id, tmp_path, speech_rate=1.0)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return Response(content=audio_bytes, media_type="audio/wav")


# --- Public routes (no auth -- consumed by podcast apps, scoped only by the
# per-show feed token embedded in the URL path itself). ---------------------

@router.get("/public/{feed_token}/feed.xml")
@limiter.limit("60/minute")
def public_feed_xml(feed_token: str, request: Request, db: Session = Depends(get_db)):
    show = _get_show_by_feed_token(feed_token, db)
    settings = get_settings()
    episodes = db.scalars(
        select(PodcastEpisode)
        .where(PodcastEpisode.show_id == show.id, PodcastEpisode.status == "ready")
        .order_by(PodcastEpisode.created_at.desc())
    ).all()
    xml = render_rss_feed(show, episodes, settings.public_base_url.rstrip("/"), settings.podcast_audio_dir)
    return Response(content=xml, media_type="application/rss+xml")


@router.get("/public/{feed_token}/cover")
@limiter.limit("60/minute")
def public_cover(feed_token: str, request: Request, db: Session = Depends(get_db)):
    show = _get_show_by_feed_token(feed_token, db)
    path = _cover_abs_path(show)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No cover image set")
    return FileResponse(path)


@router.get("/public/{feed_token}/episodes/{episode_id}/audio")
@limiter.limit("60/minute")
def public_episode_audio(feed_token: str, episode_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    show = _get_show_by_feed_token(feed_token, db)
    episode = db.scalar(
        select(PodcastEpisode).where(PodcastEpisode.id == episode_id, PodcastEpisode.show_id == show.id)
    )
    if not episode or episode.status != "ready" or not episode.audio_path:
        raise HTTPException(status_code=404, detail="Episode audio not available")
    settings = get_settings()
    full_path = os.path.join(settings.podcast_audio_dir, episode.audio_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Episode audio file missing")
    return range_response(request, full_path, media_type="audio/mpeg")
