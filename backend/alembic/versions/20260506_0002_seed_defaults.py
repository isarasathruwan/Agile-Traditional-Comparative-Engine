"""seed default admin and rule config

Revision ID: 20260506_0002
Revises: 20260506_0001
Create Date: 2026-05-06
"""

from datetime import datetime
import json
from typing import Sequence, Union

from alembic import op
from passlib.context import CryptContext
import sqlalchemy as sa


revision: str = "20260506_0002"
down_revision: Union[str, None] = "20260506_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password_hash = pwd_context.hash("admin123")

    admin_table = sa.table(
        "admin_users",
        sa.column("email", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )
    rule_table = sa.table(
        "rule_config_versions",
        sa.column("version", sa.Integer),
        sa.column("payload_json", sa.Text),
        sa.column("is_active", sa.Boolean),
        sa.column("changed_by", sa.String),
        sa.column("change_note", sa.String),
        sa.column("created_at", sa.DateTime),
    )

    connection.execute(
        sa.insert(admin_table).values(
            email="admin@methodalign.local",
            password_hash=password_hash,
            is_active=True,
            created_at=datetime.utcnow(),
        )
    )

    payload = {
        "construct_weights": {"FLEXIBILITY": 1.2, "PERFORMANCE": 1.0, "STRICTNESS": 1.1},
        "agile_baseline": {"FLEXIBILITY": 4.5, "PERFORMANCE": 3.2, "STRICTNESS": 2.7},
        "traditional_baseline": {"FLEXIBILITY": 2.8, "PERFORMANCE": 4.4, "STRICTNESS": 4.6},
        "strictness_threshold": 3.8,
    }
    connection.execute(
        sa.insert(rule_table).values(
            version=1,
            payload_json=json.dumps(payload),
            is_active=True,
            changed_by="system",
            change_note="Initial seed",
            created_at=datetime.utcnow(),
        )
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("DELETE FROM rule_config_versions WHERE version = 1")
    )
    connection.execute(
        sa.text("DELETE FROM admin_users WHERE email = 'admin@methodalign.local'")
    )
