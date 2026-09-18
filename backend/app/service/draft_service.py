import logging
import re
import uuid
import hashlib
from http import HTTPStatus
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from app.config.config import settings
from app.entity.draft_entity import AssessmentDraftEntity, AssessmentDocumentEntity
from app.entity.document_intelligence_entity import DocumentProcessingJobEntity
from app.exceptions.domain_exception import (
    ConflictException,
    NotFoundException,
    ServiceException,
    ValidationException,
)
from app.model.draft_model import (
    DraftConsentRequest,
    DraftCreateResponse,
    DraftDocumentData,
    DraftProcessingData,
    DraftStatusResponse,
)
from app.repository.draft_repository import DraftRepository
from app.service.questionnaire_service import QuestionnaireService
from app.service.rule_service import RuleService
from app.util.encryption import DocumentCipher
from app.util.response import GenericResponse

logger = logging.getLogger(__name__)


class DraftService:
    ALLOWED_CONTENT_TYPES = {"application/pdf"}
    ALLOWED_EXTENSIONS = {".pdf"}
    MAX_FILES = 5
    MAX_FILE_SIZE = 10 * 1024 * 1024
    COLLECTION_STATUSES = {"created", "collecting"}
    UPLOAD_LOCKED_STATUSES = {"processing", "ready", "failed", "submitted"}

    @staticmethod
    def _safe_filename(filename: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", filename).strip("._")
        return sanitized or "document"

    @classmethod
    def _write_file(
        cls, draft_public_id: str, content_hash: str, filename: str, file_bytes: bytes | None
    ) -> tuple[str, str | None]:
        if file_bytes is None:
            return "mock_path", None
        target_dir = Path(settings.assessment_documents_dir) / draft_public_id
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = cls._safe_filename(filename)
        target_path = target_dir / f"{content_hash[:12]}-{safe_name}.enc"
        ciphertext, nonce = DocumentCipher().encrypt(file_bytes, draft_public_id.encode("utf-8"))
        target_path.write_text(ciphertext, encoding="utf-8")
        return str(target_path), nonce

    @staticmethod
    def _token_hash(participant_token: str) -> str:
        return hashlib.sha256(participant_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _serialize_document(doc: AssessmentDocumentEntity) -> DraftDocumentData:
        return DraftDocumentData(
            id=doc.id,
            filename=doc.filename,
            content_type=doc.content_type,
            file_size=doc.file_size,
            status=doc.status,
            created_at=doc.created_at.isoformat(),
        )

    def create_draft(
        self,
        db: Session,
        assessment_session_id: str | None = None,
        participant_token: str | None = None,
    ) -> GenericResponse[DraftCreateResponse]:
        logger.info("DraftService.create_draft started")
        try:
            repository = DraftRepository(db)
            active_questionnaire = QuestionnaireService().get_active(db)
            active_rule = RuleService().get_active_rule(db)
            draft = repository.create_draft(
                AssessmentDraftEntity(
                    session_id=str(uuid.uuid4()),
                    assessment_session_id=assessment_session_id,
                    status="created",
                    participant_token_hash=self._token_hash(participant_token) if participant_token else None,
                    questionnaire_version=active_questionnaire.version,
                    rule_version=active_rule.version,
                    questionnaire_snapshot=active_questionnaire.payload_json,
                    rule_snapshot=active_rule.payload_json,
                )
            )
            if assessment_session_id:
                session = repository.get_assessment_session(assessment_session_id)
                if session:
                    session.draft_created_at = datetime.utcnow()
                    repository.save_assessment_session(session)
                    db.commit()
            data = DraftCreateResponse(draft_id=draft.session_id, status=draft.status)
            return GenericResponse.success_response("Draft created.", data=data, status_code=HTTPStatus.CREATED)
        except Exception:
            db.rollback()
            logger.exception("DraftService.create_draft failed")
            raise ServiceException("Unable to create draft.") from None

    def require_participant_access(self, db: Session, draft_id: str, participant_token: str | None) -> AssessmentDraftEntity:
        draft = DraftRepository(db).get_by_session_id(draft_id)
        if not draft:
            logger.warning("Document access denied draft_id=%s reason=draft_not_found", draft_id)
            raise NotFoundException("Draft not found")
        if not participant_token:
            logger.warning("Document access denied draft_id=%s reason=participant_cookie_missing", draft_id)
            raise ValidationException("Assessment session is not available in this browser.")
        if not draft.participant_token_hash:
            logger.warning("Document access denied draft_id=%s reason=draft_participant_token_missing", draft_id)
            raise ValidationException("Assessment session is not available in this browser.")
        if self._token_hash(participant_token) != draft.participant_token_hash:
            logger.warning("Document access denied draft_id=%s reason=participant_cookie_mismatch", draft_id)
            raise ValidationException("Assessment session is not available in this browser.")
        return draft

    def get_document_preview(
        self, db: Session, draft_id: str, document_id: int, participant_token: str | None
    ) -> tuple[bytes, str, str]:
        """Return one participant-owned document decrypted only for this response."""
        draft = self.require_participant_access(db, draft_id, participant_token)
        document = DraftRepository(db).get_document(document_id)
        if not document or document.draft_id != draft.id:
            raise NotFoundException("Document not found.")
        path = Path(document.storage_path)
        if not path.exists():
            raise NotFoundException("Document file not found.")
        try:
            if not document.encryption_nonce:
                raise ValidationException("This document cannot be previewed. Upload it again to use encrypted storage.")
            ciphertext = path.read_text(encoding="utf-8")
            content = DocumentCipher().decrypt(ciphertext, document.encryption_nonce, draft.session_id.encode("utf-8"))
            return content, document.filename, document.content_type
        except (NotFoundException, ValidationException):
            raise
        except Exception:
            logger.exception("DraftService.get_document_preview failed")
            raise ServiceException("Unable to prepare the document preview.") from None

    def record_consent(
        self, db: Session, draft_id: str, payload: DraftConsentRequest, participant_token: str | None
    ) -> GenericResponse[DraftStatusResponse]:
        logger.info(
            "Document consent requested draft_id=%s google_ai_accepted=%s research_attested=%s participant_cookie_present=%s",
            draft_id,
            payload.google_ai_processing_accepted,
            payload.research_document_attested,
            bool(participant_token),
        )
        if not payload.google_ai_processing_accepted or not payload.research_document_attested:
            logger.warning("Document consent rejected draft_id=%s reason=required_consent_missing", draft_id)
            raise ValidationException("Google AI consent and research-document attestation are required.")
        repository = DraftRepository(db)
        draft = self.require_participant_access(db, draft_id, participant_token)
        draft.consent_accepted = True
        draft.consent_policy_version = payload.consent_policy_version
        draft.consented_at = datetime.utcnow()
        draft.research_attested = True
        repository.save_draft(draft)
        logger.info("Document consent recorded draft_id=%s draft_status=%s", draft_id, draft.status)
        return GenericResponse.success_response("Consent recorded.", data=self._build_status(repository, draft))

    def add_document(
        self,
        db: Session,
        draft_id: str,
        filename: str,
        content_type: str,
        file_size: int,
        content_hash: str,
        file_bytes: bytes | None = None,
        participant_token: str | None = None,
    ) -> GenericResponse[DraftDocumentData]:
        logger.info(
            "Document upload requested draft_id=%s filename=%s content_type=%s file_size=%s participant_cookie_present=%s",
            draft_id,
            self._safe_filename(filename),
            content_type,
            file_size,
            bool(participant_token),
        )
        try:
            repository = DraftRepository(db)
            draft = repository.get_by_session_id(draft_id)
            if not draft:
                logger.warning("Document upload rejected draft_id=%s reason=draft_not_found", draft_id)
                raise NotFoundException("Draft not found")
            if file_bytes is not None:
                self._assert_participant_access(draft, participant_token)
                if not draft.consent_accepted or not draft.research_attested:
                    logger.warning(
                        "Document upload rejected draft_id=%s reason=consent_incomplete google_ai_accepted=%s research_attested=%s",
                        draft_id,
                        draft.consent_accepted,
                        draft.research_attested,
                    )
                    raise ValidationException("Confirm Google AI processing and research-document attestation before upload.")
            if draft.status not in self.COLLECTION_STATUSES:
                logger.warning("Document upload rejected draft_id=%s reason=collection_closed draft_status=%s", draft_id, draft.status)
                raise ValidationException("Document collection is closed for this assessment.")
            document_count = repository.count_documents(draft.id)
            if document_count >= self.MAX_FILES:
                logger.warning("Document upload rejected draft_id=%s reason=max_files_reached document_count=%s", draft_id, document_count)
                raise ValidationException("Maximum of 5 files allowed.")
            if file_size > self.MAX_FILE_SIZE:
                logger.warning("Document upload rejected draft_id=%s reason=file_too_large file_size=%s max_size=%s", draft_id, file_size, self.MAX_FILE_SIZE)
                raise ValidationException("File size must be under 10MB.")
            lower_name = filename.lower()
            has_allowed_extension = any(lower_name.endswith(ext) for ext in self.ALLOWED_EXTENSIONS)
            if content_type not in self.ALLOWED_CONTENT_TYPES or not has_allowed_extension:
                logger.warning(
                    "Document upload rejected draft_id=%s reason=unsupported_type content_type=%s allowed_extension=%s",
                    draft_id,
                    content_type,
                    has_allowed_extension,
                )
                raise ValidationException("Unsupported file type.")
            if file_bytes is not None and not file_bytes.startswith(b"%PDF-"):
                logger.warning("Document upload rejected draft_id=%s reason=invalid_pdf_signature", draft_id)
                raise ValidationException("The uploaded file is not a valid PDF.")
            if repository.get_document_by_hash(draft.id, content_hash):
                draft.duplicate_rejection_count += 1
                repository.save_draft(draft)
                logger.warning("Document upload rejected draft_id=%s reason=duplicate_file", draft_id)
                raise ConflictException("This file was already uploaded to the current draft.")

            storage_path, nonce = self._write_file(draft.session_id, content_hash, filename, file_bytes)
            doc = repository.create_document(
                AssessmentDocumentEntity(
                    draft_id=draft.id,
                    filename=filename,
                    content_type=content_type,
                    file_size=file_size,
                    content_hash=content_hash,
                    storage_path=storage_path,
                    status="uploaded",
                    encryption_nonce=nonce,
                    encryption_key_version=settings.document_encryption_key_version if nonce else None,
                )
            )
            if draft.status == "created":
                draft.status = "collecting"
                repository.save_draft(draft)

            data = self._serialize_document(doc)
            logger.info(
                "Document upload completed draft_id=%s document_id=%s draft_status=%s document_count=%s",
                draft_id,
                doc.id,
                draft.status,
                document_count + 1,
            )
            return GenericResponse.success_response("Document added.", data=data, status_code=HTTPStatus.CREATED)
        except (NotFoundException, ValidationException, ConflictException):
            raise
        except Exception:
            db.rollback()
            logger.exception("DraftService.add_document failed")
            raise ServiceException("Unable to add document.") from None

    def delete_document(
        self, db: Session, draft_id: str, document_id: int, participant_token: str | None
    ) -> GenericResponse[DraftStatusResponse]:
        """Remove one staged encrypted file before the participant seals the document set."""
        repository = DraftRepository(db)
        draft = self.require_participant_access(db, draft_id, participant_token)
        if draft.status not in self.COLLECTION_STATUSES:
            raise ValidationException("Documents cannot be removed after analysis has started.")
        document = repository.get_document(document_id)
        if not document or document.draft_id != draft.id:
            raise NotFoundException("Document not found.")
        try:
            path = Path(document.storage_path)
            if path.exists():
                path.unlink()
            repository.delete_document(document)
            if not repository.count_documents(draft.id):
                draft.status = "created"
                repository.save_draft(draft)
            return GenericResponse.success_response("Document removed.", data=self._build_status(repository, draft))
        except (NotFoundException, ValidationException):
            raise
        except Exception:
            db.rollback()
            logger.exception("DraftService.delete_document failed")
            raise ServiceException("Unable to remove document.") from None

    def start_document_processing(
        self, db: Session, draft_id: str, participant_token: str | None
    ) -> GenericResponse[DraftStatusResponse]:
        """Seal a collected document set and queue one complete-corpus processing job."""
        repository = DraftRepository(db)
        draft = self.require_participant_access(db, draft_id, participant_token)
        logger.info(
            "Document processing start requested draft_id=%s draft_status=%s documents=%s consent_accepted=%s research_attested=%s",
            draft_id,
            draft.status,
            repository.count_documents(draft.id),
            draft.consent_accepted,
            draft.research_attested,
        )
        if draft.status == "processing":
            return GenericResponse.success_response("Document analysis is already in progress.", data=self._build_status(repository, draft))
        if draft.status in {"ready", "failed", "submitted"}:
            logger.warning("Document processing start rejected draft_id=%s reason=already_started draft_status=%s", draft_id, draft.status)
            raise ValidationException("Document analysis has already been started for this assessment.")
        if not draft.consent_accepted or not draft.research_attested:
            logger.warning("Document processing start rejected draft_id=%s reason=consent_incomplete", draft_id)
            raise ValidationException("Confirm Google AI processing and research-document attestation before analysis.")
        if not repository.count_documents(draft.id):
            logger.warning("Document processing start rejected draft_id=%s reason=no_documents", draft_id)
            raise ValidationException("Upload at least one PDF before analysis.")
        if repository.has_active_job(draft.id):
            draft.status = "processing"
            repository.save_draft(draft)
            return GenericResponse.success_response("Document analysis is already in progress.", data=self._build_status(repository, draft))

        draft.status = "processing"
        db.add_all([draft, DocumentProcessingJobEntity(draft_id=draft.id, document_id=None, status="queued")])
        db.commit()
        db.refresh(draft)
        logger.info("Document processing queued draft_id=%s", draft_id)
        return GenericResponse.success_response(
            "Document analysis started.",
            data=self._build_status(repository, draft),
            status_code=HTTPStatus.ACCEPTED,
        )

    def _assert_participant_access(self, draft: AssessmentDraftEntity, participant_token: str | None) -> None:
        if not participant_token:
            logger.warning("Document access denied draft_id=%s reason=participant_cookie_missing", draft.session_id)
            raise ValidationException("Assessment session is not available in this browser.")
        if not draft.participant_token_hash:
            logger.warning("Document access denied draft_id=%s reason=draft_participant_token_missing", draft.session_id)
            raise ValidationException("Assessment session is not available in this browser.")
        if self._token_hash(participant_token) != draft.participant_token_hash:
            logger.warning("Document access denied draft_id=%s reason=participant_cookie_mismatch", draft.session_id)
            raise ValidationException("Assessment session is not available in this browser.")

    def _build_status(self, repository: DraftRepository, draft: AssessmentDraftEntity) -> DraftStatusResponse:
        jobs = repository.get_jobs_for_draft(draft.id)
        documents = repository.list_documents(draft.id)
        queued = sum(job.status in {"queued", "extracting", "embedding", "reasoning"} for job in jobs)
        completed = sum(job.status == "ready" for job in jobs)
        failed = sum(job.status in {"failed", "unsupported"} for job in jobs)
        active_statuses = ("reasoning", "embedding", "extracting", "queued")
        active_job = next(
            (job for status in active_statuses for job in jobs if job.status == status),
            None,
        )
        stage_metadata = {
            "queued": ("queued", "Preparing secure processing"),
            "extracting": ("extracting", "Extracting selectable document text"),
            "embedding": ("embedding", "Building the retrieval index"),
            "reasoning": ("reasoning", "Matching evidence to assessment questions"),
            "ready": ("ready", "Evidence is ready for review"),
            "failed": ("failed", "Processing needs attention"),
        }
        source_status = active_job.status if active_job else "failed" if draft.status == "failed" or failed else "ready"
        current_stage, current_stage_label = stage_metadata[source_status]
        document_by_id = {document.id: document for document in documents}
        current_document = document_by_id.get(active_job.document_id) if active_job and active_job.document_id else None
        return DraftStatusResponse(
            draft_id=draft.session_id,
            status=draft.status,
            duplicate_rejection_count=draft.duplicate_rejection_count,
            uploads_locked=draft.status in self.UPLOAD_LOCKED_STATUSES,
            documents=[self._serialize_document(document) for document in documents],
            processing=DraftProcessingData(
                status=draft.status,
                queued_jobs=queued,
                completed_jobs=completed,
                failed_jobs=failed,
                current_stage=current_stage,
                current_stage_label=current_stage_label,
                current_document_name=(
                    current_document.filename if current_document else "All uploaded documents" if active_job else None
                ),
                processed_documents=sum(document.status == "processed" for document in documents),
                total_documents=len(documents),
                message=current_stage_label if queued else None,
            ),
        )

    def get_draft_status(
        self, db: Session, draft_id: str, participant_token: str | None = None
    ) -> GenericResponse[DraftStatusResponse]:
        try:
            repository = DraftRepository(db)
            draft = repository.get_by_session_id(draft_id)
            if not draft:
                logger.warning("Document status rejected draft_id=%s reason=draft_not_found", draft_id)
                raise NotFoundException("Draft not found")
            if participant_token is not None:
                self._assert_participant_access(draft, participant_token)
            data = self._build_status(repository, draft)
            logger.info(
                "Document status fetched draft_id=%s draft_status=%s uploads_locked=%s documents=%s current_stage=%s",
                draft_id,
                draft.status,
                data.uploads_locked,
                len(data.documents),
                data.processing.current_stage,
            )
            return GenericResponse.success_response("Draft status fetched.", data=data)
        except NotFoundException:
            raise
        except Exception:
            logger.exception("DraftService.get_draft_status failed")
            raise ServiceException("Unable to fetch draft status.") from None
