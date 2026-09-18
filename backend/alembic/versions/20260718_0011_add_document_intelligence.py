"""add encrypted document intelligence pipeline

Revision ID: 20260718_0011
Revises: 20260708_0010
Create Date: 2026-07-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260718_0011"
down_revision: Union[str, None] = "20260708_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    draft_columns = _columns("assessment_drafts")
    additions = [
        ("participant_token_hash", sa.String(length=64), True),
        ("consent_accepted", sa.Boolean(), False),
        ("consent_policy_version", sa.String(length=50), True),
        ("consented_at", sa.DateTime(), True),
        ("research_attested", sa.Boolean(), False),
        ("questionnaire_version", sa.Integer(), True),
        ("rule_version", sa.Integer(), True),
        ("questionnaire_snapshot", sa.Text(), True),
        ("rule_snapshot", sa.Text(), True),
    ]
    for name, column_type, nullable in additions:
        if name not in draft_columns:
            default = "false" if name in {"consent_accepted", "research_attested"} else None
            op.add_column("assessment_drafts", sa.Column(name, column_type, nullable=nullable, server_default=default))
            if default:
                op.alter_column("assessment_drafts", name, server_default=None)
    op.create_index("ix_assessment_drafts_participant_token_hash", "assessment_drafts", ["participant_token_hash"], unique=False)

    document_columns = _columns("assessment_documents")
    if "encryption_nonce" not in document_columns:
        op.add_column("assessment_documents", sa.Column("encryption_nonce", sa.String(length=64), nullable=True))
    if "encryption_key_version" not in document_columns:
        op.add_column("assessment_documents", sa.Column("encryption_key_version", sa.String(length=50), nullable=True))

    op.create_table(
        "assessment_document_pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("assessment_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("encrypted_text", sa.Text(), nullable=False),
        sa.Column("encryption_nonce", sa.String(length=64), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("document_id", "page_number", name="uq_document_page_number"),
    )
    op.create_index("ix_assessment_document_pages_document_id", "assessment_document_pages", ["document_id"])
    op.create_table(
        "assessment_document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("draft_id", sa.Integer(), sa.ForeignKey("assessment_drafts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("assessment_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_id", sa.Integer(), sa.ForeignKey("assessment_document_pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("encrypted_text", sa.Text(), nullable=False),
        sa.Column("encryption_nonce", sa.String(length=64), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("page_id", "chunk_index", name="uq_document_chunk_index"),
    )
    op.execute("ALTER TABLE assessment_document_chunks ALTER COLUMN embedding TYPE vector(768) USING embedding::vector")
    for column in ("draft_id", "document_id", "page_id"):
        op.create_index(f"ix_assessment_document_chunks_{column}", "assessment_document_chunks", [column])
    op.execute("CREATE INDEX ix_assessment_document_chunks_embedding ON assessment_document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)")

    op.create_table(
        "assessment_document_processing_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("draft_id", sa.Integer(), sa.ForeignKey("assessment_drafts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("assessment_documents.id", ondelete="CASCADE"), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for column in ("draft_id", "document_id", "status"):
        op.create_index(f"ix_assessment_document_processing_jobs_{column}", "assessment_document_processing_jobs", [column])

    op.create_table(
        "assessment_evidence_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("draft_id", sa.Integer(), sa.ForeignKey("assessment_drafts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_key", sa.String(length=100), nullable=False),
        sa.Column("answer_type", sa.String(length=30), nullable=False),
        sa.Column("proposed_value", sa.String(length=500), nullable=True),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column("evidence_status", sa.String(length=30), nullable=False),
        sa.Column("final_value", sa.String(length=500), nullable=True),
        sa.Column("final_source", sa.String(length=30), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("draft_id", "question_key", name="uq_evidence_answer_draft_question"),
    )
    op.create_index("ix_assessment_evidence_answers_draft_id", "assessment_evidence_answers", ["draft_id"])
    op.create_table(
        "assessment_evidence_citations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evidence_answer_id", sa.Integer(), sa.ForeignKey("assessment_evidence_answers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_id", sa.Integer(), sa.ForeignKey("assessment_document_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("encrypted_excerpt", sa.Text(), nullable=False),
        sa.Column("encryption_nonce", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_assessment_evidence_citations_evidence_answer_id", "assessment_evidence_citations", ["evidence_answer_id"])
    op.create_index("ix_assessment_evidence_citations_chunk_id", "assessment_evidence_citations", ["chunk_id"])
    op.create_table(
        "assessment_document_agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("draft_id", sa.Integer(), sa.ForeignKey("assessment_drafts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_key", sa.String(length=100), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("trace_json", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_assessment_document_agent_runs_draft_id", "assessment_document_agent_runs", ["draft_id"])


def downgrade() -> None:
    for table in (
        "assessment_document_agent_runs",
        "assessment_evidence_citations",
        "assessment_evidence_answers",
        "assessment_document_processing_jobs",
        "assessment_document_chunks",
        "assessment_document_pages",
    ):
        op.drop_table(table)
