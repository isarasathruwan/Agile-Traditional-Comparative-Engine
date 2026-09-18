from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database_config import Base
from app.entity.base_mixin import TimestampMixin


class TraditionalAdvisorEntity(Base, TimestampMixin):
    """Encrypted, asynchronous delivery-method advice for Traditional results."""

    __tablename__ = "assessment_traditional_advisors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_submissions.id", ondelete="CASCADE"), unique=True, index=True
    )
    result_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_results.id", ondelete="CASCADE"), unique=True, index=True
    )
    draft_id: Mapped[int | None] = mapped_column(
        ForeignKey("assessment_drafts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    encrypted_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    encryption_nonce: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
