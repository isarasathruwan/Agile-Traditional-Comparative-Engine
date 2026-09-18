"""Add company grouping and document drafts

Revision ID: de92de000990
Revises: 20260506_0006
Create Date: 2026-07-04 21:05:51.667706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import re


# revision identifiers, used by Alembic.
revision: str = 'de92de000990'
down_revision: Union[str, None] = '20260506_0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assessment_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assessment_drafts_session_id"), "assessment_drafts", ["session_id"], unique=True)
    op.create_table(
        "assessment_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("draft_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["draft_id"], ["assessment_drafts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assessment_documents_draft_id"), "assessment_documents", ["draft_id"], unique=False)
    op.add_column("assessment_submissions", sa.Column("normalized_company", sa.String(length=255), nullable=True))
    op.add_column("assessment_submissions", sa.Column("draft_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_assessment_submissions_normalized_company"),
        "assessment_submissions",
        ["normalized_company"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_assessment_submissions_draft_id",
        "assessment_submissions",
        "assessment_drafts",
        ["draft_id"],
        ["id"],
    )

    submissions = sa.table(
        "assessment_submissions",
        sa.column("id", sa.Integer()),
        sa.column("company", sa.String()),
        sa.column("normalized_company", sa.String()),
    )
    bind = op.get_bind()
    rows = bind.execute(sa.select(submissions.c.id, submissions.c.company)).fetchall()
    for row in rows:
        normalized_company = re.sub(r"[^\w\s]", "", str(row.company or "").lower().strip())
        normalized_company = re.sub(r"\s+", " ", normalized_company)
        bind.execute(
            submissions.update()
            .where(submissions.c.id == row.id)
            .values(normalized_company=normalized_company)
        )


def downgrade() -> None:
    op.drop_constraint("fk_assessment_submissions_draft_id", "assessment_submissions", type_="foreignkey")
    op.drop_index(op.f("ix_assessment_submissions_normalized_company"), table_name="assessment_submissions")
    op.drop_column("assessment_submissions", "draft_id")
    op.drop_column("assessment_submissions", "normalized_company")
    op.drop_index(op.f("ix_assessment_documents_draft_id"), table_name="assessment_documents")
    op.drop_table("assessment_documents")
    op.drop_index(op.f("ix_assessment_drafts_session_id"), table_name="assessment_drafts")
    op.drop_table("assessment_drafts")
