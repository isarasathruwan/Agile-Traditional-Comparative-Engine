from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database_config import Base
from app.entity.base_mixin import TimestampMixin


class DocumentPageEntity(Base, TimestampMixin):
    __tablename__ = "assessment_document_pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number", name="uq_document_page_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("assessment_documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    encrypted_text: Mapped[str] = mapped_column(Text)
    encryption_nonce: Mapped[str] = mapped_column(String(64))
    character_count: Mapped[int] = mapped_column(Integer)


class DocumentChunkEntity(Base, TimestampMixin):
    __tablename__ = "assessment_document_chunks"
    __table_args__ = (UniqueConstraint("page_id", "chunk_index", name="uq_document_chunk_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("assessment_drafts.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("assessment_documents.id", ondelete="CASCADE"), index=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("assessment_document_pages.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    char_start: Mapped[int] = mapped_column(Integer)
    char_end: Mapped[int] = mapped_column(Integer)
    encrypted_text: Mapped[str] = mapped_column(Text)
    encryption_nonce: Mapped[str] = mapped_column(String(64))
    embedding: Mapped[list[float]] = mapped_column(Vector(768))


class DocumentProcessingJobEntity(Base, TimestampMixin):
    __tablename__ = "assessment_document_processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("assessment_drafts.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("assessment_documents.id", ondelete="CASCADE"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EvidenceAnswerEntity(Base, TimestampMixin):
    __tablename__ = "assessment_evidence_answers"
    __table_args__ = (UniqueConstraint("draft_id", "question_key", name="uq_evidence_answer_draft_question"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("assessment_drafts.id", ondelete="CASCADE"), index=True)
    question_key: Mapped[str] = mapped_column(String(100))
    answer_type: Mapped[str] = mapped_column(String(30))
    proposed_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), default="none")
    evidence_status: Mapped[str] = mapped_column(String(30), default="needs_input")
    final_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    final_source: Mapped[str | None] = mapped_column(String(30), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EvidenceCitationEntity(Base, TimestampMixin):
    __tablename__ = "assessment_evidence_citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_answer_id: Mapped[int] = mapped_column(ForeignKey("assessment_evidence_answers.id", ondelete="CASCADE"), index=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("assessment_document_chunks.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    char_start: Mapped[int] = mapped_column(Integer)
    char_end: Mapped[int] = mapped_column(Integer)
    encrypted_excerpt: Mapped[str] = mapped_column(Text)
    encryption_nonce: Mapped[str] = mapped_column(String(64))


class DocumentExtractedFactEntity(Base, TimestampMixin):
    """A source-backed document observation stored encrypted at rest."""

    __tablename__ = "assessment_document_extracted_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("assessment_drafts.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("assessment_documents.id", ondelete="CASCADE"), index=True)
    source_chunk_id: Mapped[int] = mapped_column(ForeignKey("assessment_document_chunks.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(160))
    encrypted_value: Mapped[str] = mapped_column(Text)
    value_encryption_nonce: Mapped[str] = mapped_column(String(64))
    encrypted_excerpt: Mapped[str] = mapped_column(Text)
    excerpt_encryption_nonce: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[str] = mapped_column(String(20), default="moderate")


class DocumentAgentRunEntity(Base, TimestampMixin):
    __tablename__ = "assessment_document_agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("assessment_drafts.id", ondelete="CASCADE"), index=True)
    question_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30))
    trace_json: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
