import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class SourceBase(BaseModel):
    name: str = Field(..., max_length=200)
    source_type: Literal["rss", "reddit", "youtube", "email"]
    config: dict = Field(default_factory=dict)
    is_active: bool = True
    fetch_interval: int = Field(default=3600, ge=300)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    config: dict | None = None
    is_active: bool | None = None
    fetch_interval: int | None = Field(None, ge=300)


class SourceOut(SourceBase):
    id: uuid.UUID
    last_fetched_at: datetime | None
    created_at: datetime
    item_count: int = 0

    model_config = {"from_attributes": True}
