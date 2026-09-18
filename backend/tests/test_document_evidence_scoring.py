import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database_config import Base
from app.entity.document_intelligence_entity import EvidenceAnswerEntity
from app.entity.draft_entity import AssessmentDraftEntity
from app.service.assessment_service import AssessmentService
from app.service.document_intelligence_service import DocumentIntelligenceService
from app.service.questionnaire_service import QuestionnaireService
from app.model.questionnaire_model import QuestionnairePayload


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _questionnaire(db):
    active = QuestionnaireService().get_active(db)
    return QuestionnairePayload.model_validate(json.loads(active.payload_json))


def test_document_questions_are_separate_from_mandatory_likert_questions():
    db = _db_session()
    questionnaire = _questionnaire(db)

    assert {item.question_id for item in questionnaire.document_questions} == {
        "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10"
    }
    assert all(not item.document_extraction.enabled for item in questionnaire.likert_questions)
    assert all(item.weight == 1.0 for item in questionnaire.document_questions)


def test_document_agent_accepts_schema_equivalent_string_chunk_ids_only():
    assert DocumentIntelligenceService._candidate_chunk_ids(
        {"evidence_chunk_ids": ["4", 8, " 12 ", "4.0", -1, 0, True, None]}
    ) == {4, 8, 12}


def test_confirmed_document_evidence_is_coverage_capped_and_missing_evidence_is_ignored():
    db = _db_session()
    questionnaire = _questionnaire(db)
    draft = AssessmentDraftEntity(session_id="evidence-score-draft")
    db.add(draft)
    db.commit()
    db.add_all(
        [
            EvidenceAnswerEntity(
                draft_id=draft.id,
                question_key="D01",
                answer_type="likert",
                proposed_value="5",
                final_value="5",
                confidence="high",
                evidence_status="suggested",
                final_source="confirmed_document",
            ),
            EvidenceAnswerEntity(
                draft_id=draft.id,
                question_key="D04",
                answer_type="likert",
                proposed_value="5",
                final_value=None,
                confidence="high",
                evidence_status="omitted",
                final_source="omitted_document",
            ),
        ]
    )
    db.commit()

    scoring, _ = AssessmentService()._evidence_scoring(
        db=db,
        draft=draft,
        questionnaire=questionnaire,
        questionnaire_construct_scores={"FLEXIBILITY": 1.0, "PERFORMANCE": 2.0, "STRICTNESS": 3.0},
    )

    assert scoring["document_coverage"]["FLEXIBILITY"] == 0.3333
    assert scoring["document_contribution"]["FLEXIBILITY"] == 0.0833
    assert scoring["decision_construct_scores"]["FLEXIBILITY"] == 1.3332
    assert scoring["document_construct_scores"]["PERFORMANCE"] is None
    assert scoring["decision_construct_scores"]["PERFORMANCE"] == 2.0
    assert scoring["decision_construct_scores"]["STRICTNESS"] == 3.0
