"""add role to admin users

Revision ID: 20260506_0005
Revises: 20260506_0004
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260506_0005"
down_revision: Union[str, None] = "20260506_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "admin_users",
        sa.Column("role", sa.String(length=50), nullable=False, server_default="super_admin"),
    )


def downgrade() -> None:
    op.drop_column("admin_users", "role")
