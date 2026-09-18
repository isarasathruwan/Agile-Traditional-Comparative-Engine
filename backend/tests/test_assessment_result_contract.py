from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database_config import Base
from app.entity.assessment_entity import (
    AssessmentAnswerEntity,
    AssessmentResultEntity,
    AssessmentSessionEntity,
    AssessmentSubmissionEntity,
)
from app.entity.draft_entity import AssessmentDocumentEntity, AssessmentDraftEntity
from app.entity.document_intelligence_entity import DocumentProcessingJobEntity, EvidenceAnswerEntity
from app.exceptions.domain_exception import ConflictException, NotFoundException, ValidationException
from app.model.assessment_model import AssessmentCreateRequest, AssessmentEventRequest
from app.service.admin_service import AdminService
from app.service.assessment_service import AssessmentService
from app.util.text_validation import validate_human_text


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _answers(**overrides: int) -> list[dict[str, object]]:
    constructs = {
        **{f"Q{number}": "FLEXIBILITY" for number in range(11, 15)},
        **{f"Q{number}": "PERFORMANCE" for number in range(15, 18)},
        **{f"Q{number}": "STRICTNESS" for number in range(18, 23)},
    }
    return [
        {"question_key": key, "construct": construct, "value": overrides.get(key, 3)}
        for key, construct in constructs.items()
    ]


def test_assessment_result_contains_dependent_scores_and_comparison_series():
    db = _db_session()
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=2),
        }
    )
    response = AssessmentService().create_assessment(db, payload)
    data = response.data

    assert data is not None
    assert "timeline_adherence" in data.dependent_variable_scores
    assert "security_integration" in data.dependent_variable_scores
    assert len(data.comparison_series["dimensions"]) == 7
    assert len(data.comparison_series["project"]) == 7
    assert len(data.comparison_series["agile"]) == 7
    assert len(data.comparison_series["traditional"]) == 7
    assert "recommended_direction" in data.insights
    assert "strongest_dimension" in data.insights
    assert data.decision_report["recommendation"] in {"Agile", "Traditional"}
    assert data.evidence_answers == []
    assert len(data.ai_demo_trace) == 5
    assert data.ai_demo_summary["demo_mode"] is True
    assert "risk_flags" in data.decision_report
    assert "hypothesis_evidence" in data.decision_report
    assert "strategy_profile" in data.decision_report
    assert "next_steps" in data.decision_report
    strategy_profile = data.decision_report["strategy_profile"]
    assert isinstance(strategy_profile, dict)
    assert "hybrid_readiness" in strategy_profile
    assert "strategy_options" in strategy_profile
    assert "Only Agile vs Traditional is empirically validated" in strategy_profile["research_boundary_note"]


def test_strategy_profile_is_advisory_and_keeps_binary_recommendation():
    db = _db_session()
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Banking & Finance",
                "org_size": "201-1,000",
                "project_name": "Core Migration",
                "project_type": "System Integration",
                "duration": "6-12 months",
                "team_size": "16-30",
                "budget": "$200K-$1M",
            },
            "answers": _answers(Q11=4, Q12=4, Q15=4, Q18=4, Q19=4),
        }
    )
    response = AssessmentService().create_assessment(db, payload)
    data = response.data

    assert data is not None
    assert data.recommendation in {"Agile", "Traditional"}
    assert data.recommendation not in {"Hybrid", "Scrum", "Kanban", "SAFe", "PRINCE2 Agile"}
    strategy_profile = data.decision_report["strategy_profile"]
    assert strategy_profile["hybrid_readiness"]["level"] in {"moderate", "high"}
    option_keys = {option["key"] for option in strategy_profile["strategy_options"]}
    assert "safe" in option_keys


def test_admin_assessment_detail_includes_profile_and_likert_answers_with_prompts():
    db = _db_session()
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=2),
        }
    )
    created = AssessmentService().create_assessment(db, payload).data
    assert created is not None

    detail = AdminService().get_assessment_detail(db, created.submission_id).data

    assert detail is not None
    assert detail.submission_id == created.submission_id
    assert len(detail.profile_answers) == 10
    assert detail.profile_answers[0].prompt == "What's your name?"
    assert detail.profile_answers[0].answer == "Tester"
    assert len(detail.likert_answers) == 12
    assert detail.likert_answers[0].question_id == "Q11"
    assert detail.likert_answers[0].prompt == "How much are requirements expected to change after development begins?"
    assert detail.likert_answers[0].answer == 4
    assert detail.ai_demo_summary["demo_mode"] is True


def test_assessment_rejects_invalid_questionnaire_option_value():
    db = _db_session()
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Invalid Industry",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=2),
        }
    )

    try:
        AssessmentService().create_assessment(db, payload)
        assert False, "Expected ValidationException"
    except ValidationException:
        assert True


def test_assessment_rejects_incomplete_or_mismatched_methodology_answers():
    db = _db_session()
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers()[:-1],
        }
    )

    try:
        AssessmentService().create_assessment(db, payload)
        assert False, "Expected ValidationException"
    except ValidationException as exc:
        assert "missing: Q22" in str(exc)


def test_assessment_accepts_other_option_with_custom_value_and_preserves_structure():
    db = _db_session()
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Other",
                "company": "Acme",
                "industry": "Other",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "Other",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "profile_other_inputs": {
                "role": "Delivery Lead",
                "industry": "Aerospace",
                "projectType": "Platform Modernization",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=2),
        }
    )

    created = AssessmentService().create_assessment(db, payload).data
    assert created is not None

    submission = db.get(AssessmentSubmissionEntity, created.submission_id)
    assert submission is not None
    assert submission.role == "Other"
    assert submission.industry == "Other"
    assert submission.project_type == "Other"
    assert submission.profile_other_inputs == {
        "role": "Delivery Lead",
        "industry": "Aerospace",
        "projectType": "Platform Modernization",
    }

    detail = AdminService().get_assessment_detail(db, created.submission_id).data
    assert detail is not None
    role_answer = next(item for item in detail.profile_answers if item.profile_key == "role")
    industry_answer = next(item for item in detail.profile_answers if item.profile_key == "industry")
    project_type_answer = next(item for item in detail.profile_answers if item.profile_key == "projectType")
    assert role_answer.answer == "Delivery Lead"
    assert role_answer.selected_option == "Other"
    assert role_answer.other_text == "Delivery Lead"
    assert industry_answer.answer == "Aerospace"
    assert project_type_answer.answer == "Platform Modernization"


def test_assessment_rejects_other_option_without_custom_value():
    db = _db_session()
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Other",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=2),
        }
    )

    try:
        AssessmentService().create_assessment(db, payload)
        assert False, "Expected ValidationException"
    except ValidationException as exc:
        assert "Please specify the other value" in str(exc)


def test_assessment_rejects_stray_custom_value_without_other_selection():
    db = _db_session()
    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "profile_other_inputs": {
                "role": "Delivery Lead",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=2),
        }
    )

    try:
        AssessmentService().create_assessment(db, payload)
        assert False, "Expected ValidationException"
    except ValidationException as exc:
        assert "Unexpected custom value" in str(exc)


def test_assessment_links_and_submits_draft():
    db = _db_session()
    draft = AssessmentDraftEntity(session_id="draft-session-1", status="uploaded")
    db.add(draft)
    db.commit()

    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=2),
            "draft_id": "draft-session-1",
        }
    )

    created = AssessmentService().create_assessment(db, payload).data
    assert created is not None

    submission = db.get(AssessmentSubmissionEntity, created.submission_id)
    refreshed_draft = db.get(AssessmentDraftEntity, draft.id)
    assert submission is not None
    assert submission.draft_id == draft.id
    assert refreshed_draft is not None
    assert refreshed_draft.status == "submitted"


def test_ai_demo_trace_counts_uploaded_documents_and_admin_analytics():
    db = _db_session()
    draft = AssessmentDraftEntity(session_id="draft-session-ai", status="uploaded")
    db.add(draft)
    db.flush()
    db.add(
        AssessmentDocumentEntity(
            draft_id=draft.id,
            filename="brief.pdf",
            content_type="application/pdf",
            file_size=2048,
            content_hash="hash-1",
            storage_path="mock_path",
            status="uploaded",
        )
    )
    draft.duplicate_rejection_count = 2
    db.commit()

    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "System Integration",
                "duration": "6-12 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=4),
            "draft_id": "draft-session-ai",
        }
    )

    created = AssessmentService().create_assessment(db, payload).data
    assert created is not None
    assert created.ai_demo_summary["documents_processed"] == 1
    assert any(step["stage"] == "extract" for step in created.ai_demo_trace)

    analytics = AdminService().get_ai_analytics(db).data
    assert analytics is not None
    assert analytics.total_documented_assessments == 1
    assert analytics.total_documents_processed == 1
    assert analytics.duplicate_rejections == 2
    assert analytics.stage_frequency["extract"] == 1


def test_assessment_workspace_analytics_tracks_session_progress_and_documents():
    db = _db_session()
    service = AssessmentService()
    session_id = "assessment-session-12345"
    service.track_event(
        db,
        AssessmentEventRequest(session_id=session_id, event="opened"),
    )
    service.track_event(
        db,
        AssessmentEventRequest(session_id=session_id, event="question_answered", question_key="Q1", question_index=1),
    )

    draft = AssessmentDraftEntity(session_id="draft-session-analytics", status="uploaded", assessment_session_id=session_id)
    db.add(draft)
    db.flush()
    db.add(
        AssessmentDocumentEntity(
            draft_id=draft.id,
            filename="brief.pdf",
            content_type="application/pdf",
            file_size=1024,
            content_hash="analytics-hash-1",
            storage_path="mock_path",
            status="uploaded",
        )
    )
    db.commit()

    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(Q11=4, Q12=4, Q13=4, Q15=3, Q16=3, Q18=4, Q19=4),
            "draft_id": "draft-session-analytics",
            "session_id": session_id,
        }
    )

    created = service.create_assessment(db, payload).data
    assert created is not None

    analytics = AdminService().get_assessment_workspace_analytics(db).data
    assert analytics is not None
    assert analytics.opened_assessments == 1
    assert analytics.answered_assessments == 1
    assert analytics.fully_answered_assessments == 1
    assert analytics.completed_submissions == 1
    assert analytics.draft_created_count == 1
    assert analytics.uploaded_document_count == 1
    assert analytics.document_backed_assessments == 1
    assert analytics.total_documents_processed == 1


def test_validate_human_text_rejects_obvious_gibberish():
    assert validate_human_text("asfsfsdas") is not None
    assert validate_human_text("sadasdaxas") is not None
    assert validate_human_text("Northstar") is None
    assert validate_human_text("Implementation roadmap") is None


def test_grouped_assessments_aggregate_normalized_company():
    db = _db_session()
    service = AssessmentService()
    for company in ("Acme, Inc.", "acme inc"):
        payload = AssessmentCreateRequest.model_validate(
            {
                "profile": {
                    "name": "Tester",
                    "role": "Project Manager",
                    "company": company,
                    "industry": "Technology",
                    "org_size": "11-50",
                    "project_name": "Pilot",
                    "project_type": "New System",
                    "duration": "3-6 months",
                    "team_size": "6-15",
                    "budget": "$10K-$50K",
                },
                "answers": _answers(Q11=4, Q15=3, Q18=2),
            }
        )
        service.create_assessment(db, payload)

    grouped = AdminService().list_grouped_assessments_by_company(
        db=db,
        page=1,
        page_size=10,
        sort_by="latest_submission_at",
        sort_dir="desc",
    ).data
    assert grouped is not None
    assert len(grouped) == 1
    assert grouped[0].submission_count == 2
    assert grouped[0].normalized_company == "acme inc"


def test_admin_delete_assessment_removes_submission_bundle_and_document_file(tmp_path):
    db = _db_session()
    session_id = "delete-session-1"
    draft = AssessmentDraftEntity(
        session_id="delete-draft-1",
        status="uploaded",
        assessment_session_id=session_id,
    )
    db.add(draft)
    db.flush()
    stored_file = tmp_path / "drafts" / "delete-draft-1" / "brief.pdf"
    stored_file.parent.mkdir(parents=True, exist_ok=True)
    stored_file.write_bytes(b"demo pdf bytes")
    db.add(
        AssessmentDocumentEntity(
            draft_id=draft.id,
            filename="brief.pdf",
            content_type="application/pdf",
            file_size=stored_file.stat().st_size,
            content_hash="delete-hash-1",
            storage_path=str(stored_file),
            status="uploaded",
        )
    )
    created_at = datetime.utcnow()
    db.add(
        AssessmentSessionEntity(
            session_id=session_id,
            status="completed",
            answered_count=22,
            last_question_key="Q22",
            opened_at=created_at,
            completed_at=created_at,
        )
    )
    db.commit()

    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(Q11=4, Q15=3, Q18=2),
            "draft_id": "delete-draft-1",
            "session_id": session_id,
        }
    )
    created = AssessmentService().create_assessment(db, payload).data
    assert created is not None

    deleted = AdminService().delete_assessment(db, created.submission_id).data
    assert deleted is not None
    assert deleted.submission_id == created.submission_id
    assert deleted.deleted_documents == 1
    assert deleted.deleted_session is True
    assert deleted.deleted_draft is True

    assert db.get(AssessmentSubmissionEntity, created.submission_id) is None
    assert db.query(AssessmentResultEntity).filter_by(submission_id=created.submission_id).first() is None
    assert db.query(AssessmentAnswerEntity).filter_by(submission_id=created.submission_id).first() is None
    assert db.query(AssessmentSessionEntity).filter_by(session_id=session_id).first() is None
    assert db.get(AssessmentDraftEntity, draft.id) is None
    assert db.query(AssessmentDocumentEntity).filter_by(draft_id=draft.id).first() is None
    assert not stored_file.exists()

    try:
        AdminService().get_assessment_detail(db, created.submission_id)
        assert False, "Expected NotFoundException"
    except NotFoundException:
        assert True


def test_admin_reset_incomplete_activity_preserves_completed_assessments(tmp_path):
    db = _db_session()
    completed_session_id = "completed-session"
    completed_draft = AssessmentDraftEntity(
        session_id="completed-draft",
        assessment_session_id=completed_session_id,
        status="uploaded",
    )
    db.add(completed_draft)
    db.flush()
    completed_file = tmp_path / "completed-draft" / "brief.pdf"
    completed_file.parent.mkdir(parents=True, exist_ok=True)
    completed_file.write_bytes(b"completed")
    completed_document = AssessmentDocumentEntity(
        draft_id=completed_draft.id,
        filename="completed.pdf",
        content_type="application/pdf",
        file_size=completed_file.stat().st_size,
        content_hash="completed-hash",
        storage_path=str(completed_file),
        status="processed",
    )
    db.add(completed_document)
    completed_at = datetime.utcnow()
    completed_session = AssessmentSessionEntity(
        session_id=completed_session_id,
        status="completed",
        answered_count=22,
        last_question_key="Q22",
        opened_at=completed_at,
        completed_at=completed_at,
    )
    db.add(completed_session)
    db.commit()

    payload = AssessmentCreateRequest.model_validate(
        {
            "profile": {
                "name": "Completed Tester",
                "role": "Project Manager",
                "company": "Acme",
                "industry": "Technology",
                "org_size": "11-50",
                "project_name": "Completed Pilot",
                "project_type": "New System",
                "duration": "3-6 months",
                "team_size": "6-15",
                "budget": "$10K-$50K",
            },
            "answers": _answers(),
            "draft_id": completed_draft.session_id,
            "session_id": completed_session_id,
        }
    )
    completed = AssessmentService().create_assessment(db, payload).data
    assert completed is not None

    incomplete_session = AssessmentSessionEntity(
        session_id="incomplete-session",
        status="in_progress",
        answered_count=4,
        last_question_key="role",
        opened_at=datetime.utcnow(),
    )
    incomplete_draft = AssessmentDraftEntity(
        session_id="incomplete-draft",
        assessment_session_id=incomplete_session.session_id,
        status="ready",
    )
    db.add_all([incomplete_session, incomplete_draft])
    db.flush()
    incomplete_file = tmp_path / "incomplete-draft" / "test.pdf"
    incomplete_file.parent.mkdir(parents=True, exist_ok=True)
    incomplete_file.write_bytes(b"incomplete")
    incomplete_document = AssessmentDocumentEntity(
        draft_id=incomplete_draft.id,
        filename="test.pdf",
        content_type="application/pdf",
        file_size=incomplete_file.stat().st_size,
        content_hash="incomplete-hash",
        storage_path=str(incomplete_file),
        status="processed",
    )
    db.add(incomplete_document)
    db.flush()
    db.add_all(
        [
            DocumentProcessingJobEntity(
                draft_id=incomplete_draft.id,
                document_id=incomplete_document.id,
                status="ready",
            ),
            EvidenceAnswerEntity(
                draft_id=incomplete_draft.id,
                question_key="DOC_Q1",
                answer_type="text",
                evidence_status="suggested",
            ),
        ]
    )
    db.commit()

    service = AdminService()
    preview = service.get_incomplete_activity(db).data
    assert preview is not None
    assert preview.incomplete_sessions == 1
    assert preview.unsubmitted_drafts == 1
    assert preview.uploaded_documents == 1
    assert preview.processing_jobs == 1
    assert preview.evidence_records == 1
    assert preview.active_processing_jobs == 0

    deleted = service.reset_incomplete_activity(db, "RESET INCOMPLETE DATA").data
    assert deleted is not None
    assert deleted.incomplete_sessions == 1
    assert deleted.unsubmitted_drafts == 1
    assert deleted.uploaded_documents == 1
    assert deleted.file_cleanup_failures == 0

    assert db.get(AssessmentSessionEntity, incomplete_session.id) is None
    assert db.get(AssessmentDraftEntity, incomplete_draft.id) is None
    assert db.get(AssessmentDocumentEntity, incomplete_document.id) is None
    assert not incomplete_file.exists()
    assert db.get(AssessmentDraftEntity, completed_draft.id) is not None
    assert db.get(AssessmentDocumentEntity, completed_document.id) is not None
    assert db.get(AssessmentSessionEntity, completed_session.id) is not None
    assert db.get(AssessmentSubmissionEntity, completed.submission_id) is not None
    assert completed_file.exists()

    summary = service.get_analytics_summary(db).data
    workspace = service.get_assessment_workspace_analytics(db).data
    assert summary is not None and summary.total_submissions == 1
    assert workspace is not None
    assert workspace.opened_assessments == 1
    assert workspace.in_progress_assessments == 0
    assert workspace.draft_created_count == 1


def test_admin_reset_incomplete_activity_rejects_active_processing_and_wrong_confirmation():
    db = _db_session()
    draft = AssessmentDraftEntity(session_id="busy-draft", status="processing")
    db.add(draft)
    db.flush()
    db.add(DocumentProcessingJobEntity(draft_id=draft.id, status="reasoning"))
    db.commit()

    service = AdminService()
    try:
        service.reset_incomplete_activity(db, "RESET")
        assert False, "Expected ValidationException"
    except ValidationException:
        assert True

    try:
        service.reset_incomplete_activity(db, "RESET INCOMPLETE DATA")
        assert False, "Expected ConflictException"
    except ConflictException:
        assert True

    assert db.get(AssessmentDraftEntity, draft.id) is not None


def test_admin_reset_incomplete_activity_allows_orphaned_processing_status(monkeypatch):
    db = _db_session()
    draft = AssessmentDraftEntity(session_id="orphaned-processing-draft", status="processing")
    db.add(draft)
    db.flush()
    db.add(DocumentProcessingJobEntity(draft_id=draft.id, status="reasoning"))
    db.commit()

    monkeypatch.setattr(
        "app.repository.assessment_repository.document_job_has_live_worker",
        lambda _db, _job_id: False,
    )

    service = AdminService()
    preview = service.get_incomplete_activity(db).data
    assert preview is not None
    assert preview.active_processing_jobs == 0

    deleted = service.reset_incomplete_activity(db, "RESET INCOMPLETE DATA").data
    assert deleted is not None
    assert deleted.unsubmitted_drafts == 1
    assert db.get(AssessmentDraftEntity, draft.id) is None
