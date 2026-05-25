import uuid
from fastapi import APIRouter, Depends, HTTPException
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
    return [_with_count(db, s) for s in sources]


@router.post("", response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    source = Source(**payload.model_dump(), user_id=current_user.id)
    db.add(source)
    db.commit()
    db.refresh(source)
    return _with_count(db, source)


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
