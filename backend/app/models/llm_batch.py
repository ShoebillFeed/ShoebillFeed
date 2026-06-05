import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LLMBatch(Base):
    __tablename__ = "llm_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anthropic_batch_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # pending → cancelling → cancelled  |  pending → completed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # list of {custom_id, item_id, item_type, is_short, social_post, item_count}
    requests: Mapped[list] = mapped_column(JSON, nullable=False)
