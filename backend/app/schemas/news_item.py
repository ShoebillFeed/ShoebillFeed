import uuid
from datetime import datetime
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field


class CategorySummary(BaseModel):
    id: uuid.UUID
    name: str
    color: str

    model_config = {"from_attributes": True}


class SourceSummary(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str

    model_config = {"from_attributes": True}


class NewsItemOut(BaseModel):
    kind: Literal["item"] = "item"
    id: uuid.UUID
    title: str
    url: str
    abstract: str | None
    extracted_keywords: list[str] | None = None
    image_url: str | None
    relevance_score: int | None
    impact_score: int | None
    llm_processed: bool
    is_read: bool
    is_relevant: bool
    read_later: bool
    published_at: datetime | None
    fetched_at: datetime
    source: SourceSummary | None = None
    categories: list[CategorySummary] = []

    model_config = {"from_attributes": True}


class ClusterItemOut(BaseModel):
    id: uuid.UUID
    title: str
    url: str
    image_url: str | None = None
    source_summary: str | None
    fetched_at: datetime
    source: SourceSummary | None = None

    model_config = {"from_attributes": True}


class NewsClusterOut(BaseModel):
    kind: Literal["cluster"] = "cluster"
    id: uuid.UUID
    title: str | None = None
    unified_abstract: str | None
    extracted_keywords: list[str] | None = None
    relevance_score: int | None
    impact_score: int | None
    is_read: bool
    last_read_at: datetime | None = None
    is_relevant: bool
    read_later: bool
    llm_processed: bool
    published_at: datetime | None
    categories: list[CategorySummary] = []
    items: list[ClusterItemOut] = []

    model_config = {"from_attributes": True}


FeedEntry = Annotated[Union[NewsItemOut, NewsClusterOut], Field(discriminator="kind")]


class NewsItemPatch(BaseModel):
    is_read: bool | None = None
    is_relevant: bool | None = None
    read_later: bool | None = None


class LLMConfigOut(BaseModel):
    llm_provider: str
    anthropic_model: str
    ollama_base_url: str
    ollama_model: str


class LLMConfigUpdate(BaseModel):
    llm_provider: str | None = None
    anthropic_model: str | None = None
    ollama_base_url: str | None = None
    ollama_model: str | None = None


class HealthOut(BaseModel):
    db: bool
    redis: bool
    llm: bool
