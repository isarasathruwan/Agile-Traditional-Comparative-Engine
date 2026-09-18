"""add questionnaire version to assessment results

Revision ID: 20260506_0004
Revises: 20260506_0003
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260506_0004"
down_revision: Union[str, None] = "20260506_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assessment_results",
        sa.Column("questionnaire_version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("assessment_results", "questionnaire_version")
