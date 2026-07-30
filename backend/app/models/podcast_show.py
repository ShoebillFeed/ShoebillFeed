import uuid
from datetime import datetime
from sqlalchemy import Boolean, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PodcastShow(Base):
    __tablename__ = "podcast_shows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # [{"id": "h1", "name": "Alex", "character_prompt": "...", "voice": "en_US-libritts_r-medium#231"}, ...]
    hosts: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    category_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"
    )
    source_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"
    )
    time_window_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    target_length_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    schedule_time: Mapped[str] = mapped_column(String(5), nullable=False, default="07:00")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    episodes: Mapped[list["PodcastEpisode"]] = relationship(
        "PodcastEpisode", back_populates="show", cascade="all, delete-orphan"
    )
