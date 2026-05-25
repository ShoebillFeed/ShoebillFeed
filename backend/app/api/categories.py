import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.models import Category, CategoryWeight, NewsItem
from app.models.news_item import news_item_categories
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.services.llm.factory import get_llm_provider

router = APIRouter()


def _build_out(db: Session, category: Category) -> CategoryOut:
    count = db.scalar(
        select(func.count()).select_from(news_item_categories)
        .where(news_item_categories.c.category_id == category.id)
    ) or 0
    out = CategoryOut.model_validate(category)
    out.item_count = count
    return out


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    categories = db.scalars(
        select(Category)
        .where(Category.user_id == current_user.id)
        .options(joinedload(Category.weight))
        .order_by(Category.name)
    ).unique().all()
    return [_build_out(db, c) for c in categories]


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    category = Category(**payload.model_dump(), user_id=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return _build_out(db, category)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(category_id: uuid.UUID, payload: CategoryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    category = db.scalar(select(Category).where(Category.id == category_id, Category.user_id == current_user.id))
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return _build_out(db, category)


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    category = db.scalar(select(Category).where(Category.id == category_id, Category.user_id == current_user.id))
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()


@router.post("/reset-weights", status_code=200)
def reset_weights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_category_ids = db.scalars(
        select(Category.id).where(Category.user_id == current_user.id)
    ).all()
    if user_category_ids:
        db.execute(
            update(CategoryWeight)
            .where(CategoryWeight.category_id.in_(user_category_ids))
            .values(weight=1.0, manual_weight=1.0, total_marked=0)
        )
    db.commit()
    return {"reset": True}


class SetManualWeightRequest(BaseModel):
    manual_weight: float = Field(..., ge=0.0, le=5.0)


@router.patch("/{category_id}/weight", response_model=CategoryOut)
def set_manual_weight(category_id: uuid.UUID, payload: SetManualWeightRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    category = db.scalar(
        select(Category).options(joinedload(Category.weight))
        .where(Category.id == category_id, Category.user_id == current_user.id)
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.weight:
        category.weight.manual_weight = payload.manual_weight
    else:
        db.add(CategoryWeight(category_id=category_id, manual_weight=payload.manual_weight))
    db.commit()
    db.refresh(category)
    return _build_out(db, category)


class GeneratePromptRequest(BaseModel):
    name: str
    keywords: list[str] = []


@router.post("/generate-prompt")
def generate_prompt(payload: GeneratePromptRequest, _: User = Depends(get_current_user)):
    if not payload.name.strip():
        raise HTTPException(status_code=422, detail="Category name is required")
    try:
        provider = get_llm_provider()
        prompt = provider.generate_category_prompt(name=payload.name.strip(), keywords=payload.keywords)
        return {"prompt": prompt.strip()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}") from exc
