import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class KeywordClusterSnapshot(Base):
    """Daily snapshot of a keyword cluster's interest weight.

    cluster_label holds the top keyword at snapshot time — used as a stable
    identity across daily refreshes so the time-series chart can connect dots
    from the same semantic cluster even when cluster_index shifts.
    """
    __tablename__ = "keyword_cluster_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    cluster_label: Mapped[str] = mapped_column(String(200), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    cluster_size: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_kc_snapshots_lookup", "user_id", "recorded_at"),
    )
