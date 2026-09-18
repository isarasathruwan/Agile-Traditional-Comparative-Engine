"""add traditional methodology advisor

Revision ID: 20260719_0014
Revises: 20260719_0013
Create Date: 2026-07-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0014"
down_revision = "20260719_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessment_traditional_advisors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("assessment_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("result_id", sa.Integer(), sa.ForeignKey("assessment_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("draft_id", sa.Integer(), sa.ForeignKey("assessment_drafts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("encrypted_payload", sa.Text(), nullable=True),
        sa.Column("encryption_nonce", sa.String(length=64), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("submission_id"),
        sa.UniqueConstraint("result_id"),
    )
    op.create_index("ix_assessment_traditional_advisors_submission_id", "assessment_traditional_advisors", ["submission_id"])
    op.create_index("ix_assessment_traditional_advisors_result_id", "assessment_traditional_advisors", ["result_id"])
    op.create_index("ix_assessment_traditional_advisors_draft_id", "assessment_traditional_advisors", ["draft_id"])
    op.create_index("ix_assessment_traditional_advisors_status", "assessment_traditional_advisors", ["status"])


def downgrade() -> None:
    op.drop_table("assessment_traditional_advisors")
