"""add profile other inputs to submissions

Revision ID: 20260708_0010
Revises: 20260705_0009
Create Date: 2026-07-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260708_0010"
down_revision: Union[str, None] = "20260705_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("assessment_submissions")}
    if "profile_other_inputs" not in columns:
        op.add_column("assessment_submissions", sa.Column("profile_other_inputs", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("assessment_submissions")}
    if "profile_other_inputs" in columns:
        op.drop_column("assessment_submissions", "profile_other_inputs")
