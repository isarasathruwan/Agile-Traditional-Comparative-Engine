import hashlib

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.config import settings
from app.config.database_config import Base
from app.exceptions.domain_exception import NotFoundException, ValidationException
from app.model.draft_model import DraftConsentRequest
from app.service.draft_service import DraftService
from app.util.encryption import DocumentCipher


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_document_cipher_round_trip_rejects_wrong_associated_data():
    cipher = DocumentCipher()
    encrypted, nonce = cipher.encrypt_text("anonymized project brief", b"draft-a")
    assert cipher.decrypt_text(encrypted, nonce, b"draft-a") == "anonymized project brief"
    with pytest.raises(Exception):
        cipher.decrypt_text(encrypted, nonce, b"draft-b")


def test_upload_requires_recorded_consent_and_persists_ciphertext(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "assessment_documents_dir", str(tmp_path))
    db = _db_session()
    service = DraftService()
    participant_token = "participant-secret"
    draft = service.create_draft(db, participant_token=participant_token).data
    assert draft is not None

    with pytest.raises(ValidationException):
        service.add_document(
            db=db,
            draft_id=draft.draft_id,
            filename="brief.pdf",
            content_type="application/pdf",
            file_size=20,
            content_hash=hashlib.sha256(b"%PDF-brief").hexdigest(),
            file_bytes=b"%PDF-brief",
            participant_token=participant_token,
        )

    service.record_consent(
        db,
        draft.draft_id,
        DraftConsentRequest(google_ai_processing_accepted=True, research_document_attested=True),
        participant_token,
    )
    created = service.add_document(
        db=db,
        draft_id=draft.draft_id,
        filename="brief.pdf",
        content_type="application/pdf",
        file_size=20,
        content_hash=hashlib.sha256(b"%PDF-brief").hexdigest(),
        file_bytes=b"%PDF-brief",
        participant_token=participant_token,
    ).data
    assert created is not None
    assert created.status == "uploaded"

    document = service.get_draft_status(db, draft.draft_id).data
    assert document is not None
    encrypted_files = list(tmp_path.rglob("*.enc"))
    assert len(encrypted_files) == 1
    assert encrypted_files[0].read_bytes() != b"%PDF-brief"

    with pytest.raises(ValidationException):
        service.require_participant_access(db, draft.draft_id, "wrong-token")


def test_participant_preview_decrypts_only_their_own_document(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "assessment_documents_dir", str(tmp_path))
    db = _db_session()
    service = DraftService()
    participant_token = "preview-owner"
    draft = service.create_draft(db, participant_token=participant_token).data
    assert draft is not None
    service.record_consent(
        db,
        draft.draft_id,
        DraftConsentRequest(google_ai_processing_accepted=True, research_document_attested=True),
        participant_token,
    )
    content = b"%PDF-preview-content"
    document = service.add_document(
        db=db,
        draft_id=draft.draft_id,
        filename="brief.pdf",
        content_type="application/pdf",
        file_size=len(content),
        content_hash=hashlib.sha256(content).hexdigest(),
        file_bytes=content,
        participant_token=participant_token,
    ).data
    assert document is not None

    preview, filename, content_type = service.get_document_preview(
        db, draft.draft_id, document.id, participant_token
    )
    assert preview == content
    assert filename == "brief.pdf"
    assert content_type == "application/pdf"

    with pytest.raises(ValidationException):
        service.get_document_preview(db, draft.draft_id, document.id, "other-browser")
    with pytest.raises(NotFoundException):
        service.get_document_preview(db, draft.draft_id, document.id + 1, participant_token)
