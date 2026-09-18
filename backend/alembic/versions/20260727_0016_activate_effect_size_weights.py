"""activate survey effect-size construct weights

Revision ID: 20260727_0016
Revises: 20260727_0015
Create Date: 2026-07-27
"""

import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260727_0016"
down_revision: Union[str, None] = "20260727_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RULE_CHANGE_NOTE = (
    "Activated provisional survey effect-size weights: FLEXIBILITY 1.37, "
    "PERFORMANCE 0.64, and STRICTNESS 0.99."
)
WEIGHTS = {"FLEXIBILITY": 1.37, "PERFORMANCE": 0.64, "STRICTNESS": 0.99}


def upgrade() -> None:
    bind = op.get_bind()
    active_rule = bind.execute(
        sa.text(
            "SELECT payload_json FROM rule_config_versions "
            "WHERE is_active = true ORDER BY version DESC LIMIT 1"
        )
    ).mappings().first()
    if not active_rule:
        raise RuntimeError("An active rule configuration is required before effect-size weights can be activated.")

    payload = json.loads(active_rule["payload_json"])
    payload["construct_weights"] = WEIGHTS
    next_version = bind.execute(
        sa.text("SELECT COALESCE(MAX(version), 0) + 1 FROM rule_config_versions")
    ).scalar_one()
    bind.execute(sa.text("UPDATE rule_config_versions SET is_active = false WHERE is_active = true"))
    bind.execute(
        sa.text(
            """
            INSERT INTO rule_config_versions
                (version, payload_json, is_active, changed_by, change_note, created_at)
            VALUES
                (:version, :payload_json, true, 'system', :change_note, CURRENT_TIMESTAMP)
            """
        ),
        {
            "version": next_version,
            "payload_json": json.dumps(payload),
            "change_note": RULE_CHANGE_NOTE,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    inserted = bind.execute(
        sa.text(
            "SELECT id FROM rule_config_versions "
            "WHERE change_note = :note ORDER BY version DESC LIMIT 1"
        ),
        {"note": RULE_CHANGE_NOTE},
    ).mappings().first()
    if not inserted:
        return

    bind.execute(
        sa.text("DELETE FROM rule_config_versions WHERE id = :id"),
        {"id": inserted["id"]},
    )
    previous = bind.execute(
        sa.text("SELECT id FROM rule_config_versions ORDER BY version DESC LIMIT 1")
    ).mappings().first()
    if previous:
        bind.execute(
            sa.text("UPDATE rule_config_versions SET is_active = true WHERE id = :id"),
            {"id": previous["id"]},
        )
