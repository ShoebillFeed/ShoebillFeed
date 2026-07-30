import uuid
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PodcastEpisode(Base):
    __tablename__ = "podcast_episodes"
    __table_args__ = (
        Index("idx_podcast_episodes_show_created", "show_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    show_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("podcast_shows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # [{"host_id": "h1", "text": "..."}, ...]
    script: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    news_item_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"
    )
    news_cluster_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"
    )
    audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    show: Mapped["PodcastShow"] = relationship("PodcastShow", back_populates="episodes")
