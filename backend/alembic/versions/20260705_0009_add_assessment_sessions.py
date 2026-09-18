"""add assessment sessions

Revision ID: 20260705_0009
Revises: 20260705_0008
Create Date: 2026-07-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260705_0009"
down_revision: Union[str, None] = "20260705_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "assessment_sessions" not in existing_tables:
        op.create_table(
            "assessment_sessions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("session_id", sa.String(length=100), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("answered_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_question_key", sa.String(length=100), nullable=True),
            sa.Column("opened_at", sa.DateTime(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("draft_created_at", sa.DateTime(), nullable=True),
            sa.Column("submission_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["submission_id"], ["assessment_submissions.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_assessment_sessions_session_id"), "assessment_sessions", ["session_id"], unique=True)

    draft_columns = {column["name"] for column in inspector.get_columns("assessment_drafts")}
    if "assessment_session_id" not in draft_columns:
        op.add_column(
            "assessment_drafts",
            sa.Column("assessment_session_id", sa.String(length=100), nullable=True),
        )
        op.create_index(
            op.f("ix_assessment_drafts_assessment_session_id"),
            "assessment_drafts",
            ["assessment_session_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    draft_columns = {column["name"] for column in inspector.get_columns("assessment_drafts")}
    draft_indexes = {index["name"] for index in inspector.get_indexes("assessment_drafts")}
    if op.f("ix_assessment_drafts_assessment_session_id") in draft_indexes:
        op.drop_index(op.f("ix_assessment_drafts_assessment_session_id"), table_name="assessment_drafts")
    if "assessment_session_id" in draft_columns:
        op.drop_column("assessment_drafts", "assessment_session_id")

    existing_tables = set(inspector.get_table_names())
    if "assessment_sessions" in existing_tables:
        op.drop_index(op.f("ix_assessment_sessions_session_id"), table_name="assessment_sessions")
        op.drop_table("assessment_sessions")
