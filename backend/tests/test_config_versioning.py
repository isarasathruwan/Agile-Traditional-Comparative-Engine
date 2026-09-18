from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database_config import Base
from app.exceptions.domain_exception import ValidationException
from app.model.admin_model import RuleConfig, RuleConfigUpdateRequest
from app.model.questionnaire_model import QuestionnairePayload, QuestionnaireUpdateRequest
from app.service.questionnaire_service import DEFAULT_QUESTIONNAIRE, QuestionnaireService
from app.service.rule_service import RuleService
from app.service.engine_service import EngineService


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_rule_version_update_and_activate():
    db = _db_session()
    service = RuleService()
    current = service.get_rule_payload(db).data
    assert current is not None
    assert current.version == 1

    update_payload = RuleConfigUpdateRequest(
        payload=RuleConfig(
            construct_weights={"FLEXIBILITY": 1.3, "PERFORMANCE": 1.0, "STRICTNESS": 1.1},
            agile_baseline={"FLEXIBILITY": 4.5, "PERFORMANCE": 3.2, "STRICTNESS": 2.7},
            traditional_baseline={"FLEXIBILITY": 2.8, "PERFORMANCE": 4.4, "STRICTNESS": 4.6},
            strictness_threshold=3.7,
        ),
        change_note="test bump",
    )
    updated = service.update_rule_payload(db, update_payload, changed_by="tester@example.com").data
    assert updated is not None
    assert updated.version == 2

    activated = service.activate_version(db, 1, changed_by="tester@example.com").data
    assert activated is not None
    assert activated.version == 1


def test_questionnaire_version_update_and_activate():
    db = _db_session()
    service = QuestionnaireService()
    active = service.get_active_payload(db).data
    assert active is not None
    assert active.version == 1

    payload = QuestionnaireUpdateRequest(
        title="Q v2",
        payload=DEFAULT_QUESTIONNAIRE,
        change_note="test questionnaire",
    )
    updated = service.create_version(db, payload, changed_by="tester@example.com").data
    assert updated is not None
    assert updated.version == 2

    activated = service.activate_version(db, 1, changed_by="tester@example.com").data
    assert activated is not None
    assert activated.version == 1


def test_survey_informed_defaults_are_anchored_and_normalized():
    db = _db_session()
    questionnaire = QuestionnaireService().get_active_payload(db).data
    rules = RuleService().get_rule_payload(db).data

    assert questionnaire is not None
    assert len(questionnaire.payload.likert_questions) == 12
    assert all(len(question.scale_labels) == 5 for question in questionnaire.payload.likert_questions)
    assert questionnaire.payload.likert_questions[0].scale_labels[0] == "Stable"

    assert rules is not None
    assert rules.payload.construct_weights == {
        "FLEXIBILITY": 1.37,
        "PERFORMANCE": 0.64,
        "STRICTNESS": 0.99,
    }
    assert sum(rules.payload.construct_weights.values()) == 3.0
    assert rules.payload.compatibility_normalization == "weighted_range"
    assert rules.payload.strictness_override_enabled is False

    result = EngineService().compute_from_construct_scores(
        {"FLEXIBILITY": 5.0, "PERFORMANCE": 1.0, "STRICTNESS": 5.0},
        rules.payload,
    )
    assert result.recommendation == "Agile"


def test_questionnaire_validation_rejects_duplicate_ids():
    db = _db_session()
    service = QuestionnaireService()
    invalid = QuestionnairePayload(
        profile_questions=[
            {
                "question_id": "Q1",
                "kind": "text",
                "profile_key": "name",
                "prompt": "Name",
                "placeholder": "Name",
            }
        ],
        likert_questions=[
            {
                "question_id": "Q1",
                "construct": "FLEXIBILITY",
                "prompt": "Flex?",
            },
            {
                "question_id": "Q2",
                "construct": "PERFORMANCE",
                "prompt": "Perf?",
            },
            {
                "question_id": "Q3",
                "construct": "STRICTNESS",
                "prompt": "Strict?",
            },
        ],
    )
    payload = QuestionnaireUpdateRequest(title="Invalid", payload=invalid)
    try:
        service.create_version(db, payload, changed_by="tester@example.com")
        assert False, "Expected ValidationException"
    except ValidationException:
        assert True
