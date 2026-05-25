import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")
    keywords: list[str] = Field(default_factory=list)
    prompt: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    keywords: list[str] | None = None
    prompt: str | None = None


class CategoryWeightOut(BaseModel):
    weight: float
    manual_weight: float = 1.0
    total_marked: int

    model_config = {"from_attributes": True}


class CategoryOut(CategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    weight: CategoryWeightOut | None = None
    item_count: int = 0

    model_config = {"from_attributes": True}
