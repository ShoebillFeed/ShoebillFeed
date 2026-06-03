import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, SmallInteger, DateTime, ForeignKey, Index, func, ARRAY, Table, Column, UniqueConstraint  # noqa: F401
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


news_item_categories = Table(
    "news_item_categories",
    Base.metadata,
    Column("news_item_id", UUID(as_uuid=True), ForeignKey("news_items.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("news_clusters.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    source_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    impact_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    llm_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_later: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_shown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    show_count: Mapped[int] = mapped_column(nullable=False, default=0)

    source: Mapped["Source"] = relationship("Source", back_populates="news_items")
    categories: Mapped[list["Category"]] = relationship("Category", secondary=news_item_categories, lazy="selectin")
    cluster: Mapped["NewsCluster | None"] = relationship("NewsCluster", back_populates="items")

    __table_args__ = (
        UniqueConstraint("user_id", "url_hash", name="uq_news_items_user_url"),
        Index("idx_news_items_url_hash", "url_hash"),  # cross-user lookup
        Index("idx_news_items_source_id", "source_id"),
        Index("idx_news_items_published_at", "published_at"),
        Index(
            "idx_news_items_relevance",
            "relevance_score",
            postgresql_where="llm_processed = true",
        ),
        Index(
            "idx_news_items_impact",
            "impact_score",
            postgresql_where="llm_processed = true",
        ),
        Index(
            "idx_news_items_read_later",
            "read_later",
            postgresql_where="read_later = true",
        ),
    )
