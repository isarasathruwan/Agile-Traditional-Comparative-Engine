"""activate survey-informed questionnaire and rule configuration

Revision ID: 20260727_0015
Revises: 20260719_0014
Create Date: 2026-07-27
"""

import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260727_0015"
down_revision: Union[str, None] = "20260719_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


QUESTIONNAIRE_CHANGE_NOTE = (
    "Activated survey-informed Version 2 with 12 anchored methodology questions."
)
RULE_CHANGE_NOTE = (
    "Activated survey-informed Version 2 centroids, equal weights, normalized distance, and no strictness override."
)


LIKERT_QUESTIONS = [
    {
        "question_id": "Q11",
        "construct": "FLEXIBILITY",
        "prompt": "How much are requirements expected to change after development begins?",
        "scale_labels": ["Stable", "Minor change", "Occasional change", "Frequent change", "Constant or substantial change"],
    },
    {
        "question_id": "Q12",
        "construct": "FLEXIBILITY",
        "prompt": "How much uncertainty exists about the final solution and its acceptance criteria?",
        "scale_labels": ["Fully defined", "Mostly defined", "Partly defined", "Significant uncertainty", "Substantial discovery required"],
    },
    {
        "question_id": "Q13",
        "construct": "FLEXIBILITY",
        "prompt": "How often can an authorized stakeholder review work and make priority decisions?",
        "scale_labels": ["Major milestones only", "Monthly", "Every 2–4 weeks", "Weekly", "Whenever needed"],
    },
    {
        "question_id": "Q14",
        "construct": "FLEXIBILITY",
        "prompt": "How capable is the team of planning, building, testing, and reviewing work in short cycles?",
        "scale_labels": ["No capability", "Limited", "Developing", "Capable", "Highly experienced"],
    },
    {
        "question_id": "Q15",
        "construct": "PERFORMANCE",
        "prompt": "How fixed is the delivery date because of contractual, legal, launch, or external commitments?",
        "scale_labels": ["Flexible", "Target only", "Important with flexibility", "Externally committed", "Immovable"],
    },
    {
        "question_id": "Q16",
        "construct": "PERFORMANCE",
        "prompt": "How fixed is the project budget or funding ceiling?",
        "scale_labels": ["Flexible", "Broad tolerance", "Moderate constraint", "Tight constraint", "No overrun permitted"],
    },
    {
        "question_id": "Q17",
        "construct": "PERFORMANCE",
        "prompt": "How much formal approval is required before the delivery plan can be changed?",
        "scale_labels": ["Team discretion", "Lightweight approval", "Manager approval", "Multiple approvals", "Contractual or board approval"],
    },
    {
        "question_id": "Q18",
        "construct": "STRICTNESS",
        "prompt": "What level of regulatory, legal, or audit obligation applies?",
        "scale_labels": ["None", "Low", "Moderate", "High", "Extensive mandatory obligations"],
    },
    {
        "question_id": "Q19",
        "construct": "STRICTNESS",
        "prompt": "What is the highest credible consequence if the system fails or is compromised?",
        "scale_labels": ["Low and reversible", "Limited", "Moderate", "Serious", "Severe or legally significant"],
    },
    {
        "question_id": "Q20",
        "construct": "STRICTNESS",
        "prompt": "How much controlled documentation and end-to-end traceability is required?",
        "scale_labels": ["Working notes", "Basic", "Standard", "Detailed", "Complete audit-grade traceability"],
    },
    {
        "question_id": "Q21",
        "construct": "STRICTNESS",
        "prompt": "How dependent is delivery on external vendors, legacy systems, or interfaces outside the team's control?",
        "scale_labels": ["Self-contained", "Few dependencies", "Moderate", "Several critical dependencies", "Many critical external dependencies"],
    },
    {
        "question_id": "Q22",
        "construct": "STRICTNESS",
        "prompt": "How much coordination and sequencing is required across teams or organizations?",
        "scale_labels": ["One small team", "Few interactions", "Multiple teams", "Distributed sequencing", "Tightly coupled multi-organization delivery"],
    },
]


PROFILE_QUESTIONS = [
    {"question_id": "Q1", "kind": "text", "profile_key": "name", "prompt": "What's your name?", "placeholder": "Your full name"},
    {"question_id": "Q2", "kind": "pill", "profile_key": "role", "prompt": "What is your role?", "options": ["Project Manager", "Software Developer", "System Architect", "IS Practitioner", "Executive", "Other"]},
    {"question_id": "Q3", "kind": "text", "profile_key": "company", "prompt": "What's your company name?", "placeholder": "Company or organization name"},
    {"question_id": "Q4", "kind": "pill", "profile_key": "industry", "prompt": "What industry are you in?", "options": ["Government", "Banking & Finance", "Healthcare", "Technology", "Telecom", "Education", "Retail", "Other"]},
    {"question_id": "Q5", "kind": "pill", "profile_key": "orgSize", "prompt": "How large is your organization?", "options": ["1-10", "11-50", "51-200", "201-1,000", "1,000+"]},
    {"question_id": "Q6", "kind": "text", "profile_key": "projectName", "prompt": "What's the name of your project?", "placeholder": "Project name"},
    {"question_id": "Q7", "kind": "pill", "profile_key": "projectType", "prompt": "What type of project is this?", "options": ["New System", "System Integration", "Upgrade & Migration", "Maintenance", "Other"]},
    {"question_id": "Q8", "kind": "pill", "profile_key": "duration", "prompt": "What is the expected project duration?", "options": ["< 3 months", "3-6 months", "6-12 months", "1-2 years", "2+ years"]},
    {"question_id": "Q9", "kind": "pill", "profile_key": "teamSize", "prompt": "How large is your project team?", "options": ["1-5", "6-15", "16-30", "30+"]},
    {"question_id": "Q10", "kind": "pill", "profile_key": "budget", "prompt": "What is the approximate budget range?", "options": ["< $10K", "$10K-$50K", "$50K-$200K", "$200K-$1M", "$1M+", "Prefer not to say"]},
]


DOCUMENT_QUESTIONS = [
    {"question_id": "D01", "construct": "FLEXIBILITY", "prompt": "The document shows that requirements are expected to materially change after delivery begins.", "weight": 1.0},
    {"question_id": "D02", "construct": "FLEXIBILITY", "prompt": "The document requires discovery, prototyping, piloting, or phased validation before the scope is settled.", "weight": 1.0},
    {"question_id": "D03", "construct": "FLEXIBILITY", "prompt": "The document commits named business stakeholders to recurring reviews, demonstrations, or feedback.", "weight": 1.0},
    {"question_id": "D04", "construct": "PERFORMANCE", "prompt": "The document establishes a fixed or externally committed delivery date.", "weight": 1.0},
    {"question_id": "D05", "construct": "PERFORMANCE", "prompt": "The document establishes a fixed budget, funding ceiling, or explicit cost-overrun constraint.", "weight": 1.0},
    {"question_id": "D06", "construct": "PERFORMANCE", "prompt": "The document requires fixed milestones, predefined deliverables, or formal acceptance before release.", "weight": 1.0},
    {"question_id": "D07", "construct": "STRICTNESS", "prompt": "The document identifies mandatory regulatory, legal, audit, or records-retention obligations.", "weight": 1.0},
    {"question_id": "D08", "construct": "STRICTNESS", "prompt": "The document requires formal security, privacy, safety, or assurance controls.", "weight": 1.0},
    {"question_id": "D09", "construct": "STRICTNESS", "prompt": "The document shows delivery depends on external vendors, legacy platforms, or multiple system interfaces.", "weight": 1.0},
    {"question_id": "D10", "construct": "STRICTNESS", "prompt": "The document requires formal change, procurement, architecture, or release approval gates.", "weight": 1.0},
]


V2_RULES = {
    "construct_weights": {"FLEXIBILITY": 1.0, "PERFORMANCE": 1.0, "STRICTNESS": 1.0},
    "agile_baseline": {"FLEXIBILITY": 4.06, "PERFORMANCE": 3.33, "STRICTNESS": 2.92},
    "traditional_baseline": {"FLEXIBILITY": 2.14, "PERFORMANCE": 4.44, "STRICTNESS": 4.44},
    "strictness_threshold": 3.8,
    "strictness_override_enabled": False,
    "compatibility_normalization": "weighted_range",
    "dependent_variable_rules": {
        "timeline_adherence": {"PERFORMANCE": 1.0},
        "budget_accuracy": {"PERFORMANCE": 1.0},
        "product_quality": {"PERFORMANCE": 0.5, "STRICTNESS": 0.5},
        "user_satisfaction": {"FLEXIBILITY": 1.0},
        "communication_effectiveness": {"FLEXIBILITY": 1.0},
        "security_integration": {"STRICTNESS": 1.0},
        "system_integration_effectiveness": {"STRICTNESS": 1.0},
    },
    "driver_rules": {
        "requirements_change": {
            "construct": "FLEXIBILITY",
            "methodology": "Agile",
            "threshold": 3.8,
            "label": "Strong adaptation and iterative-readiness signal",
        },
        "delivery_control": {
            "construct": "PERFORMANCE",
            "methodology": "Traditional",
            "threshold": 3.8,
            "label": "Strong delivery-constraint pressure",
        },
        "security_control": {
            "construct": "STRICTNESS",
            "methodology": "Traditional",
            "threshold": 3.8,
            "label": "Strong assurance and dependency pressure",
        },
    },
    "risk_flag_rules": {
        "close_call": {
            "metric": "score_gap",
            "operator": "lte",
            "threshold": 10,
            "label": "Recommendation is close; review tradeoffs before committing.",
        },
        "security_sensitive": {
            "construct": "STRICTNESS",
            "operator": "gte",
            "threshold": 3.8,
            "label": "Assurance, traceability, or dependency controls need explicit planning.",
        },
        "low_adaptability": {
            "construct": "FLEXIBILITY",
            "operator": "lte",
            "threshold": 2.5,
            "label": "Low adaptability may limit iterative delivery benefits.",
        },
    },
    "explanation_templates": {
        "Agile": "The project profile is closer to the survey-informed Agile reference where adaptation and iterative-delivery readiness are stronger.",
        "Traditional": "The project profile is closer to the survey-informed Traditional reference where delivery constraints, assurance, and dependency control are stronger.",
    },
    "next_step_templates": {
        "Agile": [
            "Confirm stakeholder availability for frequent reviews.",
            "Define short iteration goals and feedback checkpoints.",
            "Track constraint changes openly so budget and timeline impact stays visible.",
        ],
        "Traditional": [
            "Confirm the scope baseline and required approval gates before implementation.",
            "Document assurance obligations and external dependencies early.",
            "Use milestone reviews to control delivery and governance risk.",
        ],
    },
}


def upgrade() -> None:
    bind = op.get_bind()
    active_questionnaire = bind.execute(
        sa.text(
            "SELECT version, payload_json FROM questionnaire_versions "
            "WHERE is_active = true ORDER BY version DESC LIMIT 1"
        )
    ).mappings().first()
    if active_questionnaire:
        questionnaire_payload = json.loads(active_questionnaire["payload_json"])
        questionnaire_payload["likert_questions"] = LIKERT_QUESTIONS
    else:
        questionnaire_payload = {
            "profile_questions": PROFILE_QUESTIONS,
            "likert_questions": LIKERT_QUESTIONS,
            "document_questions": DOCUMENT_QUESTIONS,
        }
    questionnaire_version = bind.execute(
        sa.text("SELECT COALESCE(MAX(version), 0) + 1 FROM questionnaire_versions")
    ).scalar_one()
    bind.execute(sa.text("UPDATE questionnaire_versions SET is_active = false WHERE is_active = true"))
    bind.execute(
        sa.text(
            """
            INSERT INTO questionnaire_versions
                (version, title, payload_json, is_active, changed_by, change_note, created_at)
            VALUES
                (:version, 'Survey-Informed Questionnaire v2', :payload_json, true, 'system', :change_note, CURRENT_TIMESTAMP)
            """
        ),
        {
            "version": questionnaire_version,
            "payload_json": json.dumps(questionnaire_payload),
            "change_note": QUESTIONNAIRE_CHANGE_NOTE,
        },
    )

    rule_version = bind.execute(
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
            "version": rule_version,
            "payload_json": json.dumps(V2_RULES),
            "change_note": RULE_CHANGE_NOTE,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    questionnaire = bind.execute(
        sa.text("SELECT id FROM questionnaire_versions WHERE change_note = :note ORDER BY version DESC LIMIT 1"),
        {"note": QUESTIONNAIRE_CHANGE_NOTE},
    ).mappings().first()
    if questionnaire:
        bind.execute(sa.text("DELETE FROM questionnaire_versions WHERE id = :id"), {"id": questionnaire["id"]})
        previous = bind.execute(
            sa.text("SELECT id FROM questionnaire_versions ORDER BY version DESC LIMIT 1")
        ).mappings().first()
        if previous:
            bind.execute(sa.text("UPDATE questionnaire_versions SET is_active = true WHERE id = :id"), {"id": previous["id"]})

    rule = bind.execute(
        sa.text("SELECT id FROM rule_config_versions WHERE change_note = :note ORDER BY version DESC LIMIT 1"),
        {"note": RULE_CHANGE_NOTE},
    ).mappings().first()
    if rule:
        bind.execute(sa.text("DELETE FROM rule_config_versions WHERE id = :id"), {"id": rule["id"]})
        previous = bind.execute(
            sa.text("SELECT id FROM rule_config_versions ORDER BY version DESC LIMIT 1")
        ).mappings().first()
        if previous:
            bind.execute(sa.text("UPDATE rule_config_versions SET is_active = true WHERE id = :id"), {"id": previous["id"]})
