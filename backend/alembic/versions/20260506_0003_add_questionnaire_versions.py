"""add questionnaire versions table

Revision ID: 20260506_0003
Revises: 20260506_0002
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260506_0003"
down_revision: Union[str, None] = "20260506_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "questionnaire_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="Default Questionnaire"),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("changed_by", sa.String(length=255), nullable=False, server_default="system"),
        sa.Column("change_note", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_questionnaire_versions_version",
        "questionnaire_versions",
        ["version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_questionnaire_versions_version", table_name="questionnaire_versions")
    op.drop_table("questionnaire_versions")
