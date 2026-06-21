import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
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


def _build_out(db: Session, category: Category, source_ids: list[str] | None = None) -> CategoryOut:
    q = select(func.count()).select_from(news_item_categories).where(
        news_item_categories.c.category_id == category.id
    )
    if source_ids:
        q = q.join(NewsItem, NewsItem.id == news_item_categories.c.news_item_id).where(
            NewsItem.source_id.in_(source_ids)
        )
    count = db.scalar(q) or 0
    out = CategoryOut.model_validate(category)
    out.item_count = count
    return out


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    source_ids: list[str] | None = Query(None),
):
    categories = db.scalars(
        select(Category)
        .where(Category.user_id == current_user.id)
        .options(joinedload(Category.weight))
        .order_by(Category.name)
    ).unique().all()
    return [_build_out(db, c, source_ids) for c in categories]


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


CATEGORY_PROMPT_MAX_CHARS = 500

class GeneratePromptRequest(BaseModel):
    name: str
    keywords: list[str] = []
    max_chars: int = CATEGORY_PROMPT_MAX_CHARS


@router.post("/generate-prompt")
def generate_prompt(payload: GeneratePromptRequest, _: User = Depends(get_current_user)):
    if not payload.name.strip():
        raise HTTPException(status_code=422, detail="Category name is required")
    try:
        provider = get_llm_provider()
        prompt = provider.generate_category_prompt(
            name=payload.name.strip(),
            keywords=payload.keywords,
            max_chars=payload.max_chars,
        )
        return {"prompt": prompt.strip()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}") from exc


@router.get("/export")
def export_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    categories = db.scalars(
        select(Category).where(Category.user_id == current_user.id).order_by(Category.name)
    ).all()
    data = [
        {"name": c.name, "color": c.color, "keywords": c.keywords, "prompt": c.prompt, "taxonomy_id": c.taxonomy_id}
        for c in categories
    ]
    return JSONResponse(content=data, headers={"Content-Disposition": "attachment; filename=categories.json"})


class CategoryImportItem(BaseModel):
    name: str = Field(..., max_length=100)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")
    keywords: list[str] = Field(default_factory=list)
    prompt: str | None = None
    taxonomy_id: str | None = None


@router.post("/import", response_model=list[CategoryOut], status_code=201)
def import_categories(
    payload: list[CategoryImportItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = []
    for item in payload:
        existing = db.scalar(
            select(Category).where(Category.user_id == current_user.id, Category.name == item.name)
        )
        if existing:
            continue
        category = Category(**item.model_dump(), user_id=current_user.id)
        db.add(category)
        db.flush()
        created.append(category)
    db.commit()
    return [_build_out(db, c) for c in created]
