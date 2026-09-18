from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import pytest

from app.config.database_config import Base
from app.entity.traditional_advisor_entity import TraditionalAdvisorEntity
from app.exceptions.domain_exception import ValidationException
from app.model.assessment_model import AssessmentCreateRequest
from app.service.assessment_service import AssessmentService
from app.service.traditional_advisor_service import TraditionalAdvisorService


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _traditional_assessment(db):
    constructs = {
        **{f"Q{number}": "FLEXIBILITY" for number in range(11, 15)},
        **{f"Q{number}": "PERFORMANCE" for number in range(15, 18)},
        **{f"Q{number}": "STRICTNESS" for number in range(18, 23)},
    }
    values = {**{f"Q{number}": 1 for number in range(11, 15)}, **{f"Q{number}": 5 for number in range(15, 23)}}
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Ishara Perera",
                "role": "System Architect",
                "company": "Harbour Systems Group",
                "industry": "Government",
                "org_size": "201-1,000",
                "project_name": "Regulatory Records Migration",
                "project_type": "Upgrade & Migration",
                "duration": "1-2 years",
                "team_size": "16-30",
                "budget": "$200K-$1M",
            },
            "answers": [
                {"question_key": key, "construct": construct, "value": values[key]}
                for key, construct in constructs.items()
            ],
        }
    )
    result = AssessmentService().create_assessment(db, payload).data
    assert result is not None
    assert result.recommendation == "Traditional"
    return result


def _valid_advisor_response():
    return {
        "recommended_method": "PRINCE2",
        "recommendation_summary": "Use controlled stages and explicit governance ownership.",
        "rationale": "The project has fixed obligations, dependencies, and approval points.",
        "alternatives": [
            {"method": "V-Model", "reason": "Strong verification and traceability."},
            {"method": "Stage-Gate", "reason": "Formal investment decisions at phase boundaries."},
        ],
        "rollout": [
            {
                "phase": "Initiate",
                "objective": "Confirm authority and scope.",
                "actions": ["Approve the business case."],
                "control_artifacts": ["Project brief"],
            },
            {
                "phase": "Plan",
                "objective": "Baseline delivery controls.",
                "actions": ["Baseline scope and schedule."],
                "control_artifacts": ["Stage plan"],
            },
            {
                "phase": "Control",
                "objective": "Manage stages and exceptions.",
                "actions": ["Review stage tolerances."],
                "control_artifacts": ["Exception report"],
            },
        ],
        "tradeoffs": ["More governance effort is required."],
        "evidence": [{"claim": "Formal approvals are required.", "chunk_ids": []}],
        "limitations": ["Validate the stage boundaries with project sponsors."],
    }


def test_traditional_advisor_processes_queued_result_without_live_ai(monkeypatch):
    db = _db_session()
    result = _traditional_assessment(db)
    service = TraditionalAdvisorService()
    queued = db.scalar(
        select(TraditionalAdvisorEntity).where(TraditionalAdvisorEntity.submission_id == result.submission_id)
    )
    assert queued is not None
    assert queued.status == "queued"

    context = {
        "profile": {},
        "scores": {},
        "questionnaire_answers": [],
        "confirmed_document_answers": [],
        "extracted_facts": [],
        "retrieved_chunks": [],
    }
    monkeypatch.setattr(service, "_context", lambda *_args: (context, {}))
    monkeypatch.setattr(service, "_generate", lambda *_args: _valid_advisor_response())

    assert service.process_next_job(db) is True
    ready = service.get_for_admin(db, result.submission_id)
    assert ready.status == "ready"
    assert ready.retry_allowed is False
    assert ready.advisor is not None
    assert ready.advisor.recommended_method == "PRINCE2"
    assert len(ready.advisor.rollout) == 3
    assert any("no supporting documents" in item for item in ready.advisor.limitations)
    assert service.process_next_job(db) is False


def test_failed_advisor_can_be_retried_without_live_ai(monkeypatch):
    db = _db_session()
    result = _traditional_assessment(db)
    service = TraditionalAdvisorService()
    monkeypatch.setattr(service, "_context", lambda *_args: ({"retrieved_chunks": []}, {}))
    monkeypatch.setattr(service, "_generate", lambda *_args: (_ for _ in ()).throw(RuntimeError("provider unavailable")))
    monkeypatch.setattr("app.service.traditional_advisor_service.settings.traditional_advisor_retry_limit", 1)

    assert service.process_next_job(db) is True
    failed = service.get_for_admin(db, result.submission_id)
    assert failed.status == "failed"
    assert failed.retry_allowed is True
    assert failed.error_message == "The methodology advisory could not be generated."

    retried = service.retry(db, result.submission_id).data
    assert retried is not None
    assert retried.status == "queued"
    with pytest.raises(ValidationException):
        service.retry(db, result.submission_id)


def test_advisor_validation_rejects_duplicate_or_unsupported_methods():
    service = TraditionalAdvisorService()
    duplicate = _valid_advisor_response()
    duplicate["alternatives"][0]["method"] = "PRINCE2"
    with pytest.raises(ValidationException):
        service._validate(duplicate, {}, False)

    unsupported = _valid_advisor_response()
    unsupported["recommended_method"] = "Scrum"
    with pytest.raises(ValidationException):
        service._validate(unsupported, {}, False)
