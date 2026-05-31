import uuid
from datetime import datetime
from sqlalchemy import Text, Boolean, SmallInteger, DateTime, ForeignKey, String, func, ARRAY, Table, Column  # noqa: F401
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


news_cluster_categories = Table(
    "news_cluster_categories",
    Base.metadata,
    Column("news_cluster_id", UUID(as_uuid=True), ForeignKey("news_clusters.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class NewsCluster(Base):
    __tablename__ = "news_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    unified_abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    relevance_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    impact_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_later: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    llm_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["NewsItem"]] = relationship("NewsItem", back_populates="cluster")
    categories: Mapped[list["Category"]] = relationship("Category", secondary=news_cluster_categories, lazy="selectin")
