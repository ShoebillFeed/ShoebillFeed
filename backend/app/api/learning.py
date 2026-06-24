import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.category import Category
from app.models.category_weight import CategoryWeight
from app.models.keyword_weight import KeywordWeight
from app.models.user import User
from app.services.normalization import normalize_keyword

router = APIRouter()


class CategoryProfile(BaseModel):
    id: str
    name: str
    color: str
    learned_weight: float
    manual_weight: float
    total_marked: int


class KeywordProfile(BaseModel):
    keyword: str
    weight: float
    total_marked: int


class LearningProfile(BaseModel):
    categories: list[CategoryProfile]
    keywords: list[KeywordProfile]


class UpdateManualWeight(BaseModel):
    manual_weight: float = Field(..., ge=0.0, le=5.0)


@router.get("/profile", response_model=LearningProfile)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    categories = db.scalars(select(Category).where(Category.user_id == current_user.id)).all()
    cat_profiles = []
    for cat in categories:
        cw = db.scalar(select(CategoryWeight).where(CategoryWeight.category_id == cat.id))
        cat_profiles.append(CategoryProfile(
            id=str(cat.id),
            name=cat.name,
            color=cat.color or "#6366f1",
            learned_weight=round(cw.weight, 3) if cw else 1.0,
            manual_weight=round(cw.manual_weight, 2) if cw else 1.0,
            total_marked=cw.total_marked if cw else 0,
        ))
    cat_profiles.sort(key=lambda c: c.learned_weight * c.manual_weight, reverse=True)

    keywords = db.scalars(
        select(KeywordWeight)
        .where(KeywordWeight.user_id == current_user.id)
        .order_by(KeywordWeight.weight.desc())
        .limit(100)
    ).all()

    return LearningProfile(
        categories=cat_profiles,
        keywords=[KeywordProfile(keyword=kw.keyword, weight=round(kw.weight, 2), total_marked=kw.total_marked) for kw in keywords],
    )


@router.patch("/categories/{category_id}/weight", status_code=204)
def set_category_manual_weight(
    category_id: uuid.UUID,
    payload: UpdateManualWeight,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = db.scalar(select(Category).where(Category.id == category_id, Category.user_id == current_user.id))
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cw = db.scalar(select(CategoryWeight).where(CategoryWeight.category_id == category_id))
    if cw:
        cw.manual_weight = payload.manual_weight
    else:
        db.add(CategoryWeight(category_id=category_id, weight=1.0, manual_weight=payload.manual_weight, total_marked=0))
    db.commit()


@router.delete("/keywords/{keyword}", status_code=204)
def delete_keyword(
    keyword: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    norm = normalize_keyword(keyword)
    kw = db.get(KeywordWeight, (current_user.id, norm))
    if kw:
        db.delete(kw)
        db.commit()
