"""initial schema

Revision ID: 20260506_0001
Revises:
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260506_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)

    op.create_table(
        "rule_config_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("changed_by", sa.String(length=255), nullable=False, server_default="system"),
        sa.Column("change_note", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_rule_config_versions_version",
        "rule_config_versions",
        ["version"],
        unique=True,
    )

    op.create_table(
        "assessment_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("org_size", sa.String(length=255), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("project_type", sa.String(length=255), nullable=False),
        sa.Column("duration", sa.String(length=255), nullable=False),
        sa.Column("team_size", sa.String(length=255), nullable=False),
        sa.Column("budget", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "assessment_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("question_key", sa.String(length=100), nullable=False),
        sa.Column("construct", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["assessment_submissions.id"]),
    )

    op.create_table(
        "assessment_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("recommendation", sa.String(length=30), nullable=False),
        sa.Column("agile_score", sa.Float(), nullable=False),
        sa.Column("traditional_score", sa.Float(), nullable=False),
        sa.Column("flexibility_score", sa.Float(), nullable=False),
        sa.Column("performance_score", sa.Float(), nullable=False),
        sa.Column("strictness_score", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("rules_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["assessment_submissions.id"]),
    )


def downgrade() -> None:
    op.drop_table("assessment_results")
    op.drop_table("assessment_answers")
    op.drop_table("assessment_submissions")
    op.drop_index("ix_rule_config_versions_version", table_name="rule_config_versions")
    op.drop_table("rule_config_versions")
    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_table("admin_users")
