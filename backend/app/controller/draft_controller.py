import hashlib
import secrets

from fastapi import APIRouter, Depends, Request, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi import Query
from sqlalchemy.orm import Session

from app.config.database_config import get_db
from app.config.config import settings
from app.model.draft_model import (
    DraftConsentRequest,
    DraftCreateResponse,
    DraftDocumentData,
    DraftStatusResponse,
    EvidenceAnswerData,
    EvidenceAnswerUpdateRequest,
    DocumentExtractedFactData,
)
from app.service.draft_service import DraftService
from app.service.document_intelligence_service import DocumentIntelligenceService
from app.util.response import GenericResponse, apply_status_code

router = APIRouter()
draft_service = DraftService()
intelligence_service = DocumentIntelligenceService()


def _participant_token(request: Request) -> str | None:
    return request.cookies.get(settings.participant_cookie_name)


@router.post("", response_model=GenericResponse[DraftCreateResponse], status_code=201)
def create_draft(
    response: Response,
    assessment_session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    participant_token = secrets.token_urlsafe(32)
    service_response = draft_service.create_draft(
        db=db,
        assessment_session_id=assessment_session_id,
        participant_token=participant_token,
    )
    response.set_cookie(
        key=settings.participant_cookie_name,
        value=participant_token,
        httponly=True,
        secure=settings.participant_cookie_secure,
        samesite="lax",
        max_age=60 * 60 * 24,
        path="/",
    )
    return apply_status_code(response=response, payload=service_response)


@router.post("/{draft_id}/consent", response_model=GenericResponse[DraftStatusResponse], status_code=200)
def record_consent(
    draft_id: str,
    payload: DraftConsentRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    service_response = draft_service.record_consent(
        db=db,
        draft_id=draft_id,
        payload=payload,
        participant_token=_participant_token(request),
    )
    return apply_status_code(response=response, payload=service_response)


@router.post("/{draft_id}/documents", response_model=GenericResponse[DraftDocumentData], status_code=201)
def upload_document(
    draft_id: str,
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_bytes = file.file.read()
    file_size = len(file_bytes)
    file.file.seek(0)
    service_response = draft_service.add_document(
        db=db,
        draft_id=draft_id,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        content_hash=hashlib.sha256(file_bytes).hexdigest(),
        file_bytes=file_bytes,
        participant_token=_participant_token(request),
    )
    return apply_status_code(response=response, payload=service_response)


@router.delete("/{draft_id}/documents/{document_id}", response_model=GenericResponse[DraftStatusResponse], status_code=200)
def delete_document(
    draft_id: str,
    document_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    service_response = draft_service.delete_document(
        db=db,
        draft_id=draft_id,
        document_id=document_id,
        participant_token=_participant_token(request),
    )
    return apply_status_code(response=response, payload=service_response)


@router.post("/{draft_id}/process", response_model=GenericResponse[DraftStatusResponse], status_code=202)
def start_document_processing(
    draft_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    service_response = draft_service.start_document_processing(
        db=db,
        draft_id=draft_id,
        participant_token=_participant_token(request),
    )
    return apply_status_code(response=response, payload=service_response)


@router.get("/{draft_id}/documents/status", response_model=GenericResponse[DraftStatusResponse], status_code=200)
def get_draft_status(
    draft_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    draft_service.require_participant_access(db, draft_id, _participant_token(request))
    service_response = draft_service.get_draft_status(db=db, draft_id=draft_id)
    return apply_status_code(response=response, payload=service_response)


@router.get("/{draft_id}/documents/{document_id}/preview")
def preview_participant_document(
    draft_id: str,
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    content, filename, content_type = draft_service.get_document_preview(
        db=db,
        draft_id=draft_id,
        document_id=document_id,
        participant_token=_participant_token(request),
    )
    safe_filename = filename.replace('"', "_").replace("\n", "_").replace("\r", "_")
    return StreamingResponse(
        iter([content]),
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{safe_filename}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{draft_id}/evidence-answers", response_model=GenericResponse[list[EvidenceAnswerData]], status_code=200)
def get_evidence_answers(
    draft_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    draft_service.require_participant_access(db, draft_id, _participant_token(request))
    service_response = intelligence_service.list_evidence_answers(db=db, draft_id=draft_id)
    return apply_status_code(response=response, payload=service_response)


@router.get("/{draft_id}/document-extractions", response_model=GenericResponse[list[DocumentExtractedFactData]], status_code=200)
def get_document_extractions(
    draft_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    draft_service.require_participant_access(db, draft_id, _participant_token(request))
    service_response = intelligence_service.list_document_facts(db=db, draft_id=draft_id)
    return apply_status_code(response=response, payload=service_response)


@router.put("/{draft_id}/evidence-answers/{question_key}", response_model=GenericResponse[EvidenceAnswerData], status_code=200)
def confirm_evidence_answer(
    draft_id: str,
    question_key: str,
    payload: EvidenceAnswerUpdateRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    draft_service.require_participant_access(db, draft_id, _participant_token(request))
    service_response = intelligence_service.confirm_evidence_answer(
        db=db,
        draft_id=draft_id,
        question_key=question_key,
        payload=payload,
    )
    return apply_status_code(response=response, payload=service_response)
