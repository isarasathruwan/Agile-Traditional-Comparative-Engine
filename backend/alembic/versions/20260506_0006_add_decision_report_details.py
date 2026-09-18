"""add decision report details

Revision ID: 20260506_0006
Revises: 20260506_0005
Create Date: 2026-05-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260506_0006"
down_revision: Union[str, None] = "20260506_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assessment_results", sa.Column("dependent_variable_scores", sa.JSON(), nullable=True))
    op.add_column("assessment_results", sa.Column("comparison_series", sa.JSON(), nullable=True))
    op.add_column("assessment_results", sa.Column("decision_report", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("assessment_results", "decision_report")
    op.drop_column("assessment_results", "comparison_series")
    op.drop_column("assessment_results", "dependent_variable_scores")
