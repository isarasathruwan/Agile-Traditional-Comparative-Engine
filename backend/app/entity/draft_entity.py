from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database_config import Base
from app.entity.base_mixin import TimestampMixin


class AssessmentDraftEntity(Base, TimestampMixin):
    __tablename__ = "assessment_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    assessment_session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="created")
    duplicate_rejection_count: Mapped[int] = mapped_column(Integer, default=0)
    participant_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    consent_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_policy_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    consented_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    research_attested: Mapped[bool] = mapped_column(Boolean, default=False)
    questionnaire_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rule_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    questionnaire_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

    documents = relationship("AssessmentDocumentEntity", back_populates="draft")


class AssessmentDocumentEntity(Base, TimestampMixin):
    __tablename__ = "assessment_documents"
    __table_args__ = (UniqueConstraint("draft_id", "content_hash", name="uq_assessment_document_draft_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("assessment_drafts.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    storage_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    encryption_nonce: Mapped[str | None] = mapped_column(String(64), nullable=True)
    encryption_key_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    draft = relationship("AssessmentDraftEntity", back_populates="documents")
