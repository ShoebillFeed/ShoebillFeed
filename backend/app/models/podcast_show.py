import uuid
from datetime import datetime
from sqlalchemy import Boolean, Float, Integer, String, Text, DateTime, ForeignKey, func
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
    # Free-text concept/angle fed into the script prompt (e.g. "focus on market
    # impact, skeptical tone, skip celebrity gossip") -- shapes what the LLM
    # actually talks about and how, on top of the per-host character prompts.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    # Piper SynthesisConfig.length_scale is inverted (< 1 = faster) and pitched
    # at engineers; this is speed as a listener thinks of it (1.0 = normal,
    # 1.5 = 50% faster) -- converted at the TTS call site (length_scale = 1/rate).
    speech_rate: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    # Relative path under settings.podcast_audio_dir, e.g. "covers/<show_id>.png"
    # -- reuses the existing podcast-audio volume rather than provisioning a
    # second one just for cover art. Falls back to the app's own PWA icon
    # (already publicly served) in the RSS feed when unset.
    cover_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    public_feed_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Plaintext by design (unlike ApiToken.token_hash) -- users need to
    # re-view/re-copy this URL repeatedly without breaking existing podcast
    # app subscriptions. Still a CSPRNG token (secrets.token_urlsafe(32)),
    # equally unguessable; only retrievability differs. See services/podcast_feed.py.
    public_feed_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    episodes: Mapped[list["PodcastEpisode"]] = relationship(
        "PodcastEpisode", back_populates="show", cascade="all, delete-orphan"
    )
