import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(Text, nullable=False, default="manual")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    outline: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    images: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    image_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    full_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    wp_post_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wp_post_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    wp_slug: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("char_length(topic) >= 10 AND char_length(topic) <= 500", name="chk_topic_length"),
        CheckConstraint("mode IN ('manual', 'auto')", name="chk_mode"),
    )
