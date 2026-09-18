from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database_config import Base, get_db
from app.service.auth_service import AuthService
from main import app


def _answers(value: int = 3) -> list[dict[str, object]]:
    constructs = {
        **{f"Q{number}": "FLEXIBILITY" for number in range(11, 15)},
        **{f"Q{number}": "PERFORMANCE" for number in range(15, 18)},
        **{f"Q{number}": "STRICTNESS" for number in range(18, 23)},
    }
    return [
        {"question_key": key, "construct": construct, "value": value}
        for key, construct in constructs.items()
    ]


def _payload() -> dict[str, object]:
    return {
        "profile": {
            "name": "Maya Fernando",
            "role": "Project Manager",
            "company": "Ceylon Transit Systems",
            "industry": "Technology",
            "org_size": "51-200",
            "project_name": "Operations Renewal",
            "project_type": "Upgrade & Migration",
            "duration": "6-12 months",
            "team_size": "6-15",
            "budget": "$50K-$200K",
        },
        "answers": _answers(4),
    }


def _client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), session


def test_health_questionnaire_and_assessment_round_trip_over_http():
    client, db = _client()
    try:
        health = client.get("/health", headers={"X-Request-ID": "contract-request"})
        assert health.status_code == 200
        assert health.headers["X-Request-ID"] == "contract-request"

        questionnaire = client.get("/api/v1/questionnaire/active")
        assert questionnaire.status_code == 200
        assert len(questionnaire.json()["data"]["payload"]["likert_questions"]) == 12

        event = client.post(
            "/api/v1/assessments/events",
            json={"session_id": "contract-session", "event": "opened"},
        )
        assert event.status_code == 201
        assert event.json()["data"]["status"] == "opened"
        invalid_event = client.post(
            "/api/v1/assessments/events",
            json={"session_id": "contract-session", "event": "question_answered", "question_key": "Q1"},
        )
        assert invalid_event.status_code == 400
        assert "question_index is required" in invalid_event.json()["message"]

        created = client.post("/api/v1/assessments", json=_payload())
        assert created.status_code == 201
        result = created.json()["data"]
        assert result["recommendation"] in {"Agile", "Traditional"}
        assert result["rules_version"] >= 1
        assert result["questionnaire_version"] >= 1

        fetched = client.get(f"/api/v1/assessments/{result['submission_id']}")
        assert fetched.status_code == 200
        assert fetched.json()["data"]["recommendation"] == result["recommendation"]
        assert fetched.json()["data"]["construct_scores"] == result["construct_scores"]
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_http_validation_rejects_incomplete_assessment():
    client, db = _client()
    try:
        payload = _payload()
        payload["answers"] = _answers()[:-1]
        response = client.post("/api/v1/assessments", json=payload)
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert "missing: Q22" in response.json()["message"]
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_admin_authentication_and_authorization_over_http():
    client, db = _client()
    try:
        AuthService().seed_default_admin(db)
        unauthenticated = client.get("/api/v1/admin/me")
        assert unauthenticated.status_code == 401
        invalid_token = client.get(
            "/api/v1/admin/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert invalid_token.status_code == 401

        login = client.post(
            "/api/v1/admin/login",
            json={"email": "admin@methodalign.local", "password": "admin123"},
        )
        assert login.status_code == 200
        token = login.json()["data"]["access_token"]
        current = client.get(
            "/api/v1/admin/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert current.status_code == 200
        assert current.json()["data"]["role"] == "super_admin"
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_admin_read_workspace_contracts_over_http():
    client, db = _client()
    try:
        AuthService().seed_default_admin(db)
        created = client.post("/api/v1/assessments", json=_payload())
        assert created.status_code == 201
        submission_id = created.json()["data"]["submission_id"]
        login = client.post(
            "/api/v1/admin/login",
            json={"email": "admin@methodalign.local", "password": "admin123"},
        )
        token = login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        endpoints = [
            "/api/v1/admin/rules",
            "/api/v1/admin/rules/versions",
            "/api/v1/admin/analytics/summary",
            "/api/v1/admin/analytics/research",
            "/api/v1/admin/analytics/ai",
            "/api/v1/admin/assessments/analytics",
            "/api/v1/admin/assessments",
            "/api/v1/admin/assessment-company-groups",
            "/api/v1/admin/assessment-activity/incomplete",
            f"/api/v1/admin/assessments/{submission_id}",
            "/api/v1/admin/analytics/trends?days=30",
            "/api/v1/admin/analytics/distributions",
            "/api/v1/admin/questionnaires",
            "/api/v1/admin/users",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200, (endpoint, response.text)
            assert response.json()["success"] is True

        export = client.get("/api/v1/admin/export.csv", headers=headers)
        assert export.status_code == 200
        assert "text/csv" in export.headers["content-type"]
        assert "recommendation" in export.text
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_admin_can_preview_and_clear_incomplete_activity_over_http():
    client, db = _client()
    try:
        AuthService().seed_default_admin(db)
        opened = client.post(
            "/api/v1/assessments/events",
            json={"session_id": "cleanup-contract-session", "event": "opened"},
        )
        assert opened.status_code == 201
        draft = client.post(
            "/api/v1/assessment-drafts?assessment_session_id=cleanup-contract-session"
        )
        assert draft.status_code == 201

        login = client.post(
            "/api/v1/admin/login",
            json={"email": "admin@methodalign.local", "password": "admin123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

        preview = client.get("/api/v1/admin/assessment-activity/incomplete", headers=headers)
        assert preview.status_code == 200
        assert preview.json()["data"]["incomplete_sessions"] == 1
        assert preview.json()["data"]["unsubmitted_drafts"] == 1

        wrong_confirmation = client.request(
            "DELETE",
            "/api/v1/admin/assessment-activity/incomplete",
            headers=headers,
            json={"confirmation": "RESET"},
        )
        assert wrong_confirmation.status_code == 400

        deleted = client.request(
            "DELETE",
            "/api/v1/admin/assessment-activity/incomplete",
            headers=headers,
            json={"confirmation": "RESET INCOMPLETE DATA"},
        )
        assert deleted.status_code == 200
        assert deleted.json()["data"]["incomplete_sessions"] == 1
        assert deleted.json()["data"]["unsubmitted_drafts"] == 1

        empty_preview = client.get("/api/v1/admin/assessment-activity/incomplete", headers=headers)
        assert empty_preview.status_code == 200
        assert empty_preview.json()["data"]["incomplete_sessions"] == 0
        assert empty_preview.json()["data"]["unsubmitted_drafts"] == 0
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_participant_document_draft_lifecycle_over_http(tmp_path, monkeypatch):
    monkeypatch.setattr("app.service.draft_service.settings.assessment_documents_dir", str(tmp_path))
    client, db = _client()
    try:
        created = client.post("/api/v1/assessment-drafts?assessment_session_id=browser-session")
        assert created.status_code == 201
        draft_id = created.json()["data"]["draft_id"]
        assert "methodalign_assessment" in client.cookies

        consent = client.post(
            f"/api/v1/assessment-drafts/{draft_id}/consent",
            json={
                "consent_policy_version": "research-v1",
                "google_ai_processing_accepted": True,
                "research_document_attested": True,
            },
        )
        assert consent.status_code == 200

        upload = client.post(
            f"/api/v1/assessment-drafts/{draft_id}/documents",
            files={"file": ("governance-brief.pdf", b"%PDF-1.4 selectable test content", "application/pdf")},
        )
        assert upload.status_code == 201
        document_id = upload.json()["data"]["id"]

        status = client.get(f"/api/v1/assessment-drafts/{draft_id}/documents/status")
        assert status.status_code == 200
        assert status.json()["data"]["documents"][0]["status"] == "uploaded"

        preview = client.get(f"/api/v1/assessment-drafts/{draft_id}/documents/{document_id}/preview")
        assert preview.status_code == 200
        assert preview.content.startswith(b"%PDF-1.4")
        assert preview.headers["cache-control"] == "private, no-store"

        evidence = client.get(f"/api/v1/assessment-drafts/{draft_id}/evidence-answers")
        facts = client.get(f"/api/v1/assessment-drafts/{draft_id}/document-extractions")
        assert evidence.status_code == 200
        assert evidence.json()["data"] == []
        assert facts.status_code == 200
        assert facts.json()["data"] == []

        outsider = TestClient(app)
        denied = outsider.get(f"/api/v1/assessment-drafts/{draft_id}/documents/status")
        assert denied.status_code == 400

        removed = client.delete(f"/api/v1/assessment-drafts/{draft_id}/documents/{document_id}")
        assert removed.status_code == 200
        assert removed.json()["data"]["documents"] == []

        second_upload = client.post(
            f"/api/v1/assessment-drafts/{draft_id}/documents",
            files={"file": ("delivery-plan.pdf", b"%PDF-1.4 second selectable document", "application/pdf")},
        )
        assert second_upload.status_code == 201
        started = client.post(f"/api/v1/assessment-drafts/{draft_id}/process")
        assert started.status_code == 202
        assert started.json()["data"]["status"] == "processing"
    finally:
        app.dependency_overrides.clear()
        db.close()
