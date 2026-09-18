import hashlib

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config.database_config import Base
from app.entity.document_intelligence_entity import DocumentProcessingJobEntity
from app.model.draft_model import DraftConsentRequest
from app.repository.draft_repository import DraftRepository
from app.service.document_intelligence_service import DocumentIntelligenceService
from app.service.draft_service import DraftService


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _queued_document(db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.service.draft_service.settings.assessment_documents_dir", str(tmp_path))
    participant_token = "processing-owner"
    service = DraftService()
    draft = service.create_draft(db, participant_token=participant_token).data
    assert draft is not None
    service.record_consent(
        db,
        draft.draft_id,
        DraftConsentRequest(
            google_ai_processing_accepted=True,
            research_document_attested=True,
        ),
        participant_token,
    )
    file_bytes = b"%PDF-1.4 deterministic processing test"
    service.add_document(
        db=db,
        draft_id=draft.draft_id,
        filename="delivery-brief.pdf",
        content_type="application/pdf",
        file_size=len(file_bytes),
        content_hash=hashlib.sha256(file_bytes).hexdigest(),
        file_bytes=file_bytes,
        participant_token=participant_token,
    )
    service.start_document_processing(db, draft.draft_id, participant_token)
    return draft.draft_id


def _force_embedding_failure(monkeypatch):
    monkeypatch.setattr(DocumentIntelligenceService, "_read_document", lambda *args: b"pdf")
    monkeypatch.setattr(
        DocumentIntelligenceService,
        "_extract_pages",
        staticmethod(lambda _content: [(1, "Project constraints and governance evidence. " * 12)]),
    )
    monkeypatch.setattr(
        DocumentIntelligenceService,
        "_embed",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("503 provider unavailable")),
    )


def test_transient_provider_failure_requeues_job(tmp_path, monkeypatch):
    db = _db_session()
    draft_id = _queued_document(db, tmp_path, monkeypatch)
    _force_embedding_failure(monkeypatch)
    monkeypatch.setattr("app.service.document_intelligence_service.settings.document_worker_retry_limit", 2)

    assert DocumentIntelligenceService().process_next_job(db) is True

    repository = DraftRepository(db)
    draft = repository.get_by_session_id(draft_id)
    job = db.scalar(select(DocumentProcessingJobEntity).where(DocumentProcessingJobEntity.draft_id == draft.id))
    assert job is not None
    assert job.status == "queued"
    assert job.attempts == 1
    assert draft.status == "processing"
    assert repository.list_documents(draft.id)[0].status == "embedding"


def test_terminal_provider_failure_marks_job_draft_and_document_failed(tmp_path, monkeypatch):
    db = _db_session()
    draft_id = _queued_document(db, tmp_path, monkeypatch)
    _force_embedding_failure(monkeypatch)
    monkeypatch.setattr("app.service.document_intelligence_service.settings.document_worker_retry_limit", 1)

    assert DocumentIntelligenceService().process_next_job(db) is True

    repository = DraftRepository(db)
    draft = repository.get_by_session_id(draft_id)
    job = db.scalar(select(DocumentProcessingJobEntity).where(DocumentProcessingJobEntity.draft_id == draft.id))
    document = repository.list_documents(draft.id)[0]
    status = DraftService().get_draft_status(db, draft_id).data

    assert job is not None
    assert job.status == "failed"
    assert job.attempts == 1
    assert job.error_code == "PROCESSING_ERROR"
    assert "503 provider unavailable" in job.error_message
    assert draft.status == "failed"
    assert document.status == "failed"
    assert status is not None
    assert status.status == "failed"
    assert status.processing.current_stage == "failed"
    assert status.processing.failed_jobs == 1
