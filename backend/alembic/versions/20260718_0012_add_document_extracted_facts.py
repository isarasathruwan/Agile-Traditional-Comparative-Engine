"""add encrypted document fact extraction

Revision ID: 20260718_0012
Revises: 20260718_0011
Create Date: 2026-07-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260718_0012"
down_revision: Union[str, None] = "20260718_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assessment_document_extracted_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("draft_id", sa.Integer(), sa.ForeignKey("assessment_drafts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("assessment_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_chunk_id", sa.Integer(), sa.ForeignKey("assessment_document_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("value_encryption_nonce", sa.String(length=64), nullable=False),
        sa.Column("encrypted_excerpt", sa.Text(), nullable=False),
        sa.Column("excerpt_encryption_nonce", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for column in ("draft_id", "document_id", "source_chunk_id"):
        op.create_index(
            f"ix_assessment_document_extracted_facts_{column}",
            "assessment_document_extracted_facts",
            [column],
        )


def downgrade() -> None:
    op.drop_table("assessment_document_extracted_facts")
