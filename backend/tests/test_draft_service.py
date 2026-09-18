from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database_config import Base
import hashlib
import pytest
from sqlalchemy import select

from app.entity.document_intelligence_entity import DocumentProcessingJobEntity
from app.exceptions.domain_exception import ConflictException, ValidationException
from app.model.draft_model import DraftConsentRequest
from app.service.draft_service import DraftService


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_draft_lifecycle_and_limits():
    db = _db_session()
    service = DraftService()

    draft = service.create_draft(db).data
    assert draft is not None
    assert draft.status == "created"

    created = service.add_document(
        db=db,
        draft_id=draft.draft_id,
        filename="brief.pdf",
        content_type="application/pdf",
        file_size=1024,
        content_hash=hashlib.sha256(b"brief").hexdigest(),
    ).data
    assert created is not None
    assert created.status == "uploaded"

    status = service.get_draft_status(db, draft.draft_id).data
    assert status is not None
    assert status.status == "collecting"
    assert status.duplicate_rejection_count == 0
    assert len(status.documents) == 1
    assert status.uploads_locked is False


def test_draft_rejects_invalid_file_type():
    db = _db_session()
    service = DraftService()
    draft = service.create_draft(db).data
    assert draft is not None

    try:
        service.add_document(
            db=db,
            draft_id=draft.draft_id,
            filename="notes.txt",
            content_type="text/plain",
            file_size=128,
            content_hash=hashlib.sha256(b"notes").hexdigest(),
        )
        assert False, "Expected ValidationException"
    except ValidationException:
        assert True


def test_draft_rejects_duplicate_document_within_same_draft():
    db = _db_session()
    service = DraftService()
    draft = service.create_draft(db).data
    assert draft is not None
    content_hash = hashlib.sha256(b"same-content").hexdigest()

    service.add_document(
        db=db,
        draft_id=draft.draft_id,
        filename="brief.pdf",
        content_type="application/pdf",
        file_size=1024,
        content_hash=content_hash,
    )

    try:
        service.add_document(
            db=db,
            draft_id=draft.draft_id,
            filename="brief-copy.pdf",
            content_type="application/pdf",
            file_size=1024,
            content_hash=content_hash,
        )
        assert False, "Expected ConflictException"
    except ConflictException:
        status = service.get_draft_status(db, draft.draft_id).data
        assert status is not None
        assert status.duplicate_rejection_count == 1


def test_document_collection_stays_staged_until_explicit_batch_start(tmp_path, monkeypatch):
    monkeypatch.setattr("app.service.draft_service.settings.assessment_documents_dir", str(tmp_path))
    db = _db_session()
    service = DraftService()
    participant_token = "batch-owner"
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
    for filename in ("brief-a.pdf", "brief-b.pdf"):
        content = f"%PDF-{filename}".encode()
        service.add_document(
            db=db,
            draft_id=draft.draft_id,
            filename=filename,
            content_type="application/pdf",
            file_size=len(content),
            content_hash=hashlib.sha256(content).hexdigest(),
            file_bytes=content,
            participant_token=participant_token,
        )

    assert list(db.scalars(select(DocumentProcessingJobEntity))) == []
    staged = service.get_draft_status(db, draft.draft_id).data
    assert staged is not None
    service.delete_document(db, draft.draft_id, staged.documents[1].id, participant_token)
    assert len(service.get_draft_status(db, draft.draft_id).data.documents) == 1

    started = service.start_document_processing(db, draft.draft_id, participant_token).data
    assert started is not None
    assert started.status == "processing"
    assert started.uploads_locked is True
    jobs = list(db.scalars(select(DocumentProcessingJobEntity)))
    assert len(jobs) == 1
    assert jobs[0].document_id is None
    assert service.start_document_processing(db, draft.draft_id, participant_token).data.status == "processing"
    assert len(list(db.scalars(select(DocumentProcessingJobEntity)))) == 1

    with pytest.raises(ValidationException):
        service.add_document(
            db=db,
            draft_id=draft.draft_id,
            filename="late.pdf",
            content_type="application/pdf",
            file_size=12,
            content_hash=hashlib.sha256(b"%PDF-late").hexdigest(),
            file_bytes=b"%PDF-late",
            participant_token=participant_token,
        )
