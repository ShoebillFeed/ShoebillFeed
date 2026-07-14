import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import Source, NewsItem
from app.models.user import User
from app.schemas.source import SourceCreate, SourceUpdate, SourceOut

router = APIRouter()


def _with_count(db: Session, source: Source) -> SourceOut:
    count = db.scalar(select(func.count()).where(NewsItem.source_id == source.id)) or 0
    out = SourceOut.model_validate(source)
    out.item_count = count
    return out


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sources = db.scalars(
        select(Source).where(Source.user_id == current_user.id).order_by(Source.created_at)
    ).all()

    # Single GROUP BY instead of N+1 per-source COUNT queries
    ids = [s.id for s in sources]
    counts: dict = {}
    if ids:
        rows = db.execute(
            select(NewsItem.source_id, func.count().label("cnt"))
            .where(NewsItem.source_id.in_(ids))
            .group_by(NewsItem.source_id)
        )
        counts = {row.source_id: row.cnt for row in rows}

    result = []
    for s in sources:
        out = SourceOut.model_validate(s)
        out.item_count = counts.get(s.id, 0)
        result.append(out)
    return result


def _check_scraper_robots(config: dict) -> None:
    """Raise if a scraper source's URL is disallowed by the site's robots.txt."""
    url = (config.get("url") or "").strip()
    if not url:
        return
    from app.services.fetchers.scraper import robots_allowed

    if not robots_allowed(url):
        raise HTTPException(
            status_code=403,
            detail="This site's robots.txt disallows automated scraping. This source cannot be added.",
        )


@router.post("", response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.source_type == "scraper":
        _check_scraper_robots(payload.config)
    source = Source(**payload.model_dump(), user_id=current_user.id)
    db.add(source)
    db.commit()
    db.refresh(source)
    return _with_count(db, source)


_SAFE_TYPES = {"rss", "atom", "mastodon", "arxiv", "lemmy", "github", "bluesky", "telegram", "scraper"}


@router.get("/shared", response_model=list[SourceOut])
def list_shared_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Sources configured by other users that the current user has not yet added.
    Credential-bearing types (email, reddit) are excluded."""
    # Names+types already owned by the current user
    owned = set(
        db.execute(
            select(func.lower(Source.name), Source.source_type)
            .where(Source.user_id == current_user.id)
        ).all()
    )

    sources = db.scalars(
        select(Source)
        .where(Source.user_id != current_user.id, Source.source_type.in_(_SAFE_TYPES))
        .order_by(func.lower(Source.name))
    ).all()

    seen: set[tuple] = set()
    result: list[SourceOut] = []
    for s in sources:
        key = (s.name.lower(), s.source_type)
        if key in seen or key in owned:
            continue
        seen.add(key)
        count = db.scalar(select(func.count()).where(NewsItem.source_id == s.id)) or 0
        out = SourceOut.model_validate(s)
        out.item_count = count
        result.append(out)

    return result


@router.get("/export")
def export_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sources = db.scalars(
        select(Source).where(Source.user_id == current_user.id).order_by(Source.created_at)
    ).all()
    data = [
        {"name": s.name, "source_type": s.source_type, "config": s.config, "is_active": s.is_active, "fetch_interval": s.fetch_interval}
        for s in sources
    ]
    return JSONResponse(content=data, headers={"Content-Disposition": "attachment; filename=sources.json"})


@router.post("/import", response_model=list[SourceOut], status_code=201)
def import_sources(
    payload: list[SourceCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = []
    for item in payload:
        existing = db.scalar(
            select(Source).where(Source.user_id == current_user.id, Source.name == item.name)
        )
        if existing:
            continue
        if item.source_type == "scraper":
            try:
                _check_scraper_robots(item.config)
            except HTTPException:
                continue
        source = Source(**item.model_dump(), user_id=current_user.id)
        db.add(source)
        db.flush()
        created.append(source)
    db.commit()
    return [_with_count(db, s) for s in created]


class ScraperSuggestRequest(BaseModel):
    url: str


@router.post("/scraper/suggest")
def suggest_scraper_config(payload: ScraperSuggestRequest, _: User = Depends(get_current_user)):
    """Fetch a page and use the configured LLM to suggest CSS selectors for
    its article list, so non-experts don't have to inspect HTML by hand."""
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=422, detail="URL is required")

    from app.services.fetchers.scraper import RobotsDisallowedError
    from app.services.scraper_assist import suggest_scraper_config as _suggest

    try:
        return _suggest(url)
    except RobotsDisallowedError:
        raise HTTPException(status_code=403, detail="This site's robots.txt disallows automated scraping")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not analyze page: {exc}") from exc


@router.get("/{source_id}", response_model=SourceOut)
def get_source(source_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    source = db.scalar(select(Source).where(Source.id == source_id, Source.user_id == current_user.id))
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return _with_count(db, source)


@router.patch("/{source_id}", response_model=SourceOut)
def update_source(source_id: uuid.UUID, payload: SourceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    source = db.scalar(select(Source).where(Source.id == source_id, Source.user_id == current_user.id))
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.source_type == "scraper" and payload.config is not None:
        _check_scraper_robots(payload.config)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return _with_count(db, source)


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    source = db.scalar(select(Source).where(Source.id == source_id, Source.user_id == current_user.id))
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()


@router.post("/{source_id}/fetch")
def trigger_fetch(source_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    source = db.scalar(select(Source).where(Source.id == source_id, Source.user_id == current_user.id))
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    from app.tasks.fetch_tasks import fetch_source
    fetch_source.apply_async(args=[str(source_id)], queue="fetch")
    return {"queued": True}


@router.post("/fetch-all")
def fetch_all(_: User = Depends(get_current_user)):
    from app.tasks.fetch_tasks import fetch_all_sources
    fetch_all_sources.apply_async(queue="fetch")
    return {"queued": True}
