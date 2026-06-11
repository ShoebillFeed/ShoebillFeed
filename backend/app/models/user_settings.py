import uuid
from sqlalchemy import Boolean, Float, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    llm_min_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    weight_base: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    weight_log_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    relevance_llm_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    relevance_learning_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    relevance_cluster_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    stats_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    output_language: Mapped[str | None] = mapped_column(String(10), nullable=True, default=None)
    time_decay_param: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    show_decay_param: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mark_shown_delay_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    learning_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    ignore_penalty_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.1)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    push_min_relevance: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    push_top_category_percent: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    push_all_categories: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_category_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    push_all_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_source_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    push_cluster_per_source: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    push_all_tabs: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_tab_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
