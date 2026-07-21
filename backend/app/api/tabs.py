import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.user_tab import UserTab

router = APIRouter()

# Curated so a custom tab's icon is never confused with an icon that already
# means something specific elsewhere in the app (e.g. Bookmark = Read Later,
# TrendingUp = Impact sort). Keep in sync with frontend/src/lib/tabIcons.ts.
TAB_ICONS = (
    "star", "heart", "flag", "globe", "compass", "flame", "rocket", "coffee",
    "home", "briefcase", "music", "camera", "gamepad2", "sparkles", "trophy",
    "lightbulb", "gift", "graduationcap", "mic", "rss", "layers", "mappin",
    "leaf", "pawprint",
)
TabIcon = Literal[TAB_ICONS]


class UserTabOut(BaseModel):
    id: uuid.UUID
    name: str
    sort: str
    category_ids: list[uuid.UUID] = []
    source_ids: list[uuid.UUID] = []
    unread_only: bool = False
    position: int = 0
    icon: str | None = None

    model_config = {"from_attributes": True}


class UserTabCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sort: Literal["newest", "relevant", "impact"] = "newest"
    category_ids: list[uuid.UUID] = []
    source_ids: list[uuid.UUID] = []
    unread_only: bool = False
    icon: TabIcon | None = None


class UserTabUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    sort: Literal["newest", "relevant", "impact"] | None = None
    category_ids: list[uuid.UUID] | None = None
    source_ids: list[uuid.UUID] | None = None
    unread_only: bool | None = None
    position: int | None = None
    icon: TabIcon | None = None


def _get(tab_id: uuid.UUID, db: Session, user_id: uuid.UUID) -> UserTab:
    tab = db.scalar(select(UserTab).where(UserTab.id == tab_id, UserTab.user_id == user_id))
    if not tab:
        raise HTTPException(status_code=404, detail="Tab not found")
    return tab


@router.get("", response_model=list[UserTabOut])
def list_tabs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.scalars(
        select(UserTab)
        .where(UserTab.user_id == current_user.id)
        .order_by(UserTab.position, UserTab.name)
    ).all()


@router.post("", response_model=UserTabOut, status_code=201)
def create_tab(
    payload: UserTabCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    max_pos = db.scalar(
        select(UserTab.position)
        .where(UserTab.user_id == current_user.id)
        .order_by(UserTab.position.desc())
    ) or 0
    tab = UserTab(
        user_id=current_user.id,
        name=payload.name,
        sort=payload.sort,
        category_ids=payload.category_ids,
        source_ids=payload.source_ids,
        unread_only=payload.unread_only,
        icon=payload.icon,
        position=max_pos + 1,
    )
    db.add(tab)
    db.commit()
    db.refresh(tab)
    return tab


@router.patch("/{tab_id}", response_model=UserTabOut)
def update_tab(
    tab_id: uuid.UUID,
    payload: UserTabUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tab = _get(tab_id, db, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tab, field, value)
    db.commit()
    db.refresh(tab)
    return tab


@router.delete("/{tab_id}", status_code=204)
def delete_tab(
    tab_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tab = _get(tab_id, db, current_user.id)
    db.delete(tab)
    db.commit()
