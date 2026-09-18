"""add missing draft_id to assessment submissions

Revision ID: 20260705_0007
Revises: de92de000990
Create Date: 2026-07-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260705_0007"
down_revision: Union[str, None] = "de92de000990"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("assessment_submissions")}
    if "draft_id" not in existing_columns:
        op.add_column("assessment_submissions", sa.Column("draft_id", sa.Integer(), nullable=True))

    existing_foreign_keys = {
        tuple(foreign_key.get("constrained_columns", [])): foreign_key
        for foreign_key in inspector.get_foreign_keys("assessment_submissions")
    }
    if ("draft_id",) not in existing_foreign_keys:
        op.create_foreign_key(
            "fk_assessment_submissions_draft_id",
            "assessment_submissions",
            "assessment_drafts",
            ["draft_id"],
            ["id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("assessment_submissions")}
    existing_foreign_keys = {
        tuple(foreign_key.get("constrained_columns", [])): foreign_key
        for foreign_key in inspector.get_foreign_keys("assessment_submissions")
    }
    if ("draft_id",) in existing_foreign_keys:
        op.drop_constraint("fk_assessment_submissions_draft_id", "assessment_submissions", type_="foreignkey")
    if "draft_id" in existing_columns:
        op.drop_column("assessment_submissions", "draft_id")
