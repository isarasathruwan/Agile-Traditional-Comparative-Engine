"""add ai demo trace and document hashes

Revision ID: 20260705_0008
Revises: 20260705_0007
Create Date: 2026-07-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260705_0008"
down_revision: Union[str, None] = "20260705_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    draft_columns = {column["name"] for column in inspector.get_columns("assessment_drafts")}
    if "duplicate_rejection_count" not in draft_columns:
        op.add_column(
            "assessment_drafts",
            sa.Column("duplicate_rejection_count", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("assessment_drafts", "duplicate_rejection_count", server_default=None)

    document_columns = {column["name"] for column in inspector.get_columns("assessment_documents")}
    if "content_hash" not in document_columns:
        op.add_column(
            "assessment_documents",
            sa.Column("content_hash", sa.String(length=64), nullable=True),
        )
        op.create_index(
            op.f("ix_assessment_documents_content_hash"),
            "assessment_documents",
            ["content_hash"],
            unique=False,
        )
        op.execute(
            "UPDATE assessment_documents "
            "SET content_hash = md5(draft_id::text || ':' || id::text || ':' || filename || ':' || file_size::text)"
        )
        op.alter_column("assessment_documents", "content_hash", nullable=False)

    unique_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("assessment_documents")}
    if "uq_assessment_document_draft_hash" not in unique_constraints:
        op.create_unique_constraint(
            "uq_assessment_document_draft_hash",
            "assessment_documents",
            ["draft_id", "content_hash"],
        )

    result_columns = {column["name"] for column in inspector.get_columns("assessment_results")}
    if "ai_demo_trace" not in result_columns:
        op.add_column("assessment_results", sa.Column("ai_demo_trace", sa.JSON(), nullable=True))
    if "ai_demo_summary" not in result_columns:
        op.add_column("assessment_results", sa.Column("ai_demo_summary", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    result_columns = {column["name"] for column in inspector.get_columns("assessment_results")}
    if "ai_demo_summary" in result_columns:
        op.drop_column("assessment_results", "ai_demo_summary")
    if "ai_demo_trace" in result_columns:
        op.drop_column("assessment_results", "ai_demo_trace")

    document_columns = {column["name"] for column in inspector.get_columns("assessment_documents")}
    unique_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("assessment_documents")}
    if "uq_assessment_document_draft_hash" in unique_constraints:
        op.drop_constraint("uq_assessment_document_draft_hash", "assessment_documents", type_="unique")
    indexes = {index["name"] for index in inspector.get_indexes("assessment_documents")}
    if op.f("ix_assessment_documents_content_hash") in indexes:
        op.drop_index(op.f("ix_assessment_documents_content_hash"), table_name="assessment_documents")
    if "content_hash" in document_columns:
        op.drop_column("assessment_documents", "content_hash")

    draft_columns = {column["name"] for column in inspector.get_columns("assessment_drafts")}
    if "duplicate_rejection_count" in draft_columns:
        op.drop_column("assessment_drafts", "duplicate_rejection_count")
