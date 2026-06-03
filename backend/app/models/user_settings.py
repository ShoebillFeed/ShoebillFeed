import uuid
from sqlalchemy import Boolean, Float, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    llm_min_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    weight_base: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    weight_log_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    relevance_llm_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    relevance_learning_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    relevance_cluster_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    stats_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    output_language: Mapped[str | None] = mapped_column(String(10), nullable=True, default=None)
    time_decay_param: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    show_decay_param: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
