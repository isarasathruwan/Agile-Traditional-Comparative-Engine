"""activate versioned document-only evidence questions

Revision ID: 20260719_0013
Revises: 20260718_0012
Create Date: 2026-07-19
"""

import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260719_0013"
down_revision: Union[str, None] = "20260718_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DOCUMENT_QUESTIONS = [
    ("D01", "FLEXIBILITY", "The document shows that requirements are expected to materially change after delivery begins."),
    ("D02", "FLEXIBILITY", "The document requires discovery, prototyping, piloting, or phased validation before the scope is settled."),
    ("D03", "FLEXIBILITY", "The document commits named business stakeholders to recurring reviews, demonstrations, or feedback."),
    ("D04", "PERFORMANCE", "The document establishes a fixed or externally committed delivery date."),
    ("D05", "PERFORMANCE", "The document establishes a fixed budget, funding ceiling, or explicit cost-overrun constraint."),
    ("D06", "PERFORMANCE", "The document requires fixed milestones, predefined deliverables, or formal acceptance before release."),
    ("D07", "STRICTNESS", "The document identifies mandatory regulatory, legal, audit, or records-retention obligations."),
    ("D08", "STRICTNESS", "The document requires formal security, privacy, safety, or assurance controls."),
    ("D09", "STRICTNESS", "The document shows delivery depends on external vendors, legacy platforms, or multiple system interfaces."),
    ("D10", "STRICTNESS", "The document requires formal change, procurement, architecture, or release approval gates."),
]


def _document_questions() -> list[dict[str, object]]:
    return [
        {
            "question_id": question_id,
            "construct": construct,
            "prompt": prompt,
            "weight": 1.0,
            "document_extraction": {
                "enabled": True,
                "answer_type": "likert",
                "instruction": "Use only direct, cited document evidence. Do not infer missing facts.",
                "rubric": "Score 1 for explicit low or absent evidence, 3 for explicit bounded or mixed evidence, and 5 for explicit high, fixed, or mandatory evidence. Return no answer when unsupported.",
            },
        }
        for question_id, construct, prompt in DOCUMENT_QUESTIONS
    ]


def upgrade() -> None:
    bind = op.get_bind()
    active = bind.execute(
        sa.text("SELECT id, version, title, payload_json FROM questionnaire_versions WHERE is_active = true ORDER BY version DESC LIMIT 1")
    ).mappings().first()
    if not active:
        return

    payload = json.loads(active["payload_json"])
    if payload.get("document_questions"):
        return
    for question in [*payload.get("profile_questions", []), *payload.get("likert_questions", [])]:
        config = question.get("document_extraction") or {}
        config.update({"enabled": False, "answer_type": config.get("answer_type", "likert")})
        question["document_extraction"] = config
    payload["document_questions"] = _document_questions()
    next_version = bind.execute(sa.text("SELECT COALESCE(MAX(version), 0) + 1 FROM questionnaire_versions")).scalar_one()
    bind.execute(sa.text("UPDATE questionnaire_versions SET is_active = false WHERE is_active = true"))
    bind.execute(
        sa.text(
            """
            INSERT INTO questionnaire_versions (version, title, payload_json, is_active, changed_by, change_note, created_at)
            VALUES (:version, :title, :payload_json, true, 'system', :change_note, CURRENT_TIMESTAMP)
            """
        ),
        {
            "version": next_version,
            "title": f"{active['title']} - Document Evidence",
            "payload_json": json.dumps(payload),
            "change_note": "Added D01-D10 optional document-only evidence instrument; mandatory questionnaire extraction disabled.",
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    inserted = bind.execute(
        sa.text(
            "SELECT id, version FROM questionnaire_versions WHERE change_note = :note ORDER BY version DESC LIMIT 1"
        ),
        {"note": "Added D01-D10 optional document-only evidence instrument; mandatory questionnaire extraction disabled."},
    ).mappings().first()
    if not inserted:
        return
    bind.execute(sa.text("DELETE FROM questionnaire_versions WHERE id = :id"), {"id": inserted["id"]})
    previous = bind.execute(
        sa.text("SELECT id FROM questionnaire_versions ORDER BY version DESC LIMIT 1")
    ).mappings().first()
    if previous:
        bind.execute(sa.text("UPDATE questionnaire_versions SET is_active = true WHERE id = :id"), {"id": previous["id"]})
