import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class PodcastHostSchema(BaseModel):
    # crypto.randomUUID() (used client-side) produces a 36-char string
    # (8-4-4-4-12 hex + 4 hyphens) -- give real headroom above that.
    id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=50)
    character_prompt: str = Field(..., max_length=1000)
    voice: str = Field(..., max_length=100)


class PodcastShowBase(BaseModel):
    name: str = Field(..., max_length=200)
    hosts: list[PodcastHostSchema] = Field(..., min_length=1, max_length=3)
    category_ids: list[uuid.UUID] = Field(default_factory=list)
    source_ids: list[uuid.UUID] = Field(default_factory=list)
    time_window_hours: int = Field(default=24, ge=1, le=168)
    target_length_minutes: int = Field(default=10, ge=1, le=15)
    language: str = Field(default="en", max_length=10)
    schedule_time: str = Field(default="07:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: str = Field(default="UTC", max_length=64)
    is_active: bool = True


class PodcastShowCreate(PodcastShowBase):
    pass


class PodcastShowUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    hosts: list[PodcastHostSchema] | None = Field(None, min_length=1, max_length=3)
    category_ids: list[uuid.UUID] | None = None
    source_ids: list[uuid.UUID] | None = None
    time_window_hours: int | None = Field(None, ge=1, le=168)
    target_length_minutes: int | None = Field(None, ge=1, le=15)
    language: str | None = Field(None, max_length=10)
    schedule_time: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: str | None = Field(None, max_length=64)
    is_active: bool | None = None


class PodcastShowOut(PodcastShowBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    public_feed_enabled: bool = False
    # Server-computed from public_feed_token + settings.public_base_url at
    # response time -- the raw token is never exposed as its own field, only
    # this assembled URL (or null when disabled/not yet generated).
    public_feed_url: str | None = None

    model_config = {"from_attributes": True}


class PodcastScriptTurnSchema(BaseModel):
    host_id: str
    text: str


class PodcastEpisodeOut(BaseModel):
    id: uuid.UUID
    show_id: uuid.UUID
    show_name: str = ""
    status: Literal["pending", "generating", "ready", "failed"]
    script: list[PodcastScriptTurnSchema] | None = None
    news_item_ids: list[uuid.UUID] = []
    news_cluster_ids: list[uuid.UUID] = []
    duration_seconds: int | None = None
    error_message: str | None = None
    created_at: datetime
    generated_at: datetime | None = None

    model_config = {"from_attributes": True}


class VoiceOut(BaseModel):
    id: str
    label: str
