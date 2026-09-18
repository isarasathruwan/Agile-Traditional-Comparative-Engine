from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.config import settings
from app.entity.assessment_entity import AssessmentResultEntity, AssessmentSubmissionEntity
from app.entity.document_intelligence_entity import DocumentChunkEntity, DocumentPageEntity
from app.entity.traditional_advisor_entity import TraditionalAdvisorEntity
from app.exceptions.domain_exception import NotFoundException, ServiceException, ValidationException
from app.model.traditional_advisor_model import TraditionalAdvisorData, TraditionalAdvisorPayload
from app.repository.assessment_repository import AssessmentRepository
from app.repository.draft_repository import DraftRepository
from app.service.document_intelligence_service import DocumentIntelligenceService
from app.service.gemini_rate_limiter import GeminiRequestLimiter
from app.util.encryption import DocumentCipher
from app.util.response import GenericResponse

logger = logging.getLogger(__name__)


class TraditionalAdvisorService:
    """Creates a bounded, evidence-cited Traditional delivery recommendation."""

    METHODS = {
        "Waterfall": "Stable requirements, fixed dependencies, and sequential delivery milestones.",
        "V-Model": "Verification, validation, traceability, and assurance-heavy delivery.",
        "PRINCE2": "Defined governance roles, business justification, and controlled stages.",
        "Stage-Gate": "Investment decisions, phase approvals, and formal go/no-go controls.",
        "PMBOK Predictive Governance": "Baselined scope, schedule, cost, risk, and change control.",
    }
    RETRIEVAL_QUERIES = [
        "project scope requirements milestones dependencies delivery constraints",
        "governance approvals stakeholders business case stage gates",
        "risk compliance security verification validation testing traceability",
        "budget schedule baseline change control project management",
    ]

    @staticmethod
    def _aad(submission: AssessmentSubmissionEntity, draft) -> bytes:
        return (draft.session_id if draft else f"assessment:{submission.id}").encode("utf-8")

    @staticmethod
    def _hash(token: str | None) -> str:
        return hashlib.sha256((token or "").encode("utf-8")).hexdigest()

    def queue_for_result(
        self,
        db: Session,
        submission: AssessmentSubmissionEntity,
        result: AssessmentResultEntity,
    ) -> TraditionalAdvisorData:
        if result.recommendation != "Traditional":
            return TraditionalAdvisorData(submission_id=submission.id, status="not_applicable")
        entity = db.scalar(
            select(TraditionalAdvisorEntity).where(TraditionalAdvisorEntity.submission_id == submission.id)
        )
        if not entity:
            entity = TraditionalAdvisorEntity(
                submission_id=submission.id,
                result_id=result.id,
                draft_id=submission.draft_id,
                status="queued",
            )
            db.add(entity)
            db.commit()
            db.refresh(entity)
        return self._serialize(db, entity, submission)

    def _serialize(
        self, db: Session, entity: TraditionalAdvisorEntity | None, submission: AssessmentSubmissionEntity, include_payload: bool = True
    ) -> TraditionalAdvisorData:
        if not entity:
            return TraditionalAdvisorData(submission_id=submission.id, status="not_applicable")
        payload = None
        if include_payload and entity.status == "ready" and entity.encrypted_payload and entity.encryption_nonce:
            draft = AssessmentRepository(db).get_draft_by_id(entity.draft_id) if entity.draft_id else None
            try:
                payload = TraditionalAdvisorPayload.model_validate_json(
                    DocumentCipher().decrypt_text(entity.encrypted_payload, entity.encryption_nonce, self._aad(submission, draft))
                )
            except Exception:
                logger.exception("Unable to decrypt traditional advisor payload submission_id=%s", submission.id)
                return TraditionalAdvisorData(
                    submission_id=submission.id,
                    status="failed",
                    retry_allowed=True,
                    error_message="The advisory result could not be read. Retry the advisory.",
                )
        return TraditionalAdvisorData(
            submission_id=submission.id,
            status=entity.status,
            retry_allowed=entity.status == "failed",
            generated_at=entity.completed_at,
            error_message=entity.error_message if entity.status == "failed" else None,
            advisor=payload,
        )

    def get_for_participant(
        self, db: Session, submission_id: int, participant_token: str | None
    ) -> GenericResponse[TraditionalAdvisorData]:
        repo = AssessmentRepository(db)
        submission = repo.get_submission_by_id(submission_id)
        if not submission:
            raise NotFoundException("Assessment not found.")
        draft = repo.get_draft_by_id(submission.draft_id) if submission.draft_id else None
        if not draft or not draft.participant_token_hash or not hmac.compare_digest(draft.participant_token_hash, self._hash(participant_token)):
            raise ValidationException("Assessment session is not available in this browser.")
        entity = db.scalar(select(TraditionalAdvisorEntity).where(TraditionalAdvisorEntity.submission_id == submission_id))
        return GenericResponse.success_response("Traditional advisor status fetched.", data=self._serialize(db, entity, submission))

    def get_for_admin(self, db: Session, submission_id: int) -> TraditionalAdvisorData:
        repo = AssessmentRepository(db)
        submission = repo.get_submission_by_id(submission_id)
        if not submission:
            raise NotFoundException("Assessment not found.")
        entity = db.scalar(select(TraditionalAdvisorEntity).where(TraditionalAdvisorEntity.submission_id == submission_id))
        return self._serialize(db, entity, submission)

    def retry(self, db: Session, submission_id: int) -> GenericResponse[TraditionalAdvisorData]:
        submission = AssessmentRepository(db).get_submission_by_id(submission_id)
        entity = db.scalar(select(TraditionalAdvisorEntity).where(TraditionalAdvisorEntity.submission_id == submission_id))
        if not submission or not entity:
            raise NotFoundException("Traditional advisor record not found.")
        if entity.status != "failed":
            raise ValidationException("Only a failed advisory can be retried.")
        entity.status = "queued"
        entity.error_code = None
        entity.error_message = None
        entity.encrypted_payload = None
        entity.encryption_nonce = None
        entity.completed_at = None
        db.add(entity)
        db.commit()
        return GenericResponse.success_response("Traditional advisor queued.", data=self._serialize(db, entity, submission, False))

    def _context(self, db: Session, entity: TraditionalAdvisorEntity) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
        repo = AssessmentRepository(db)
        draft_repo = DraftRepository(db)
        submission = repo.get_submission_by_id(entity.submission_id)
        result = repo.get_result_by_submission_id(entity.submission_id)
        draft = repo.get_draft_by_id(submission.draft_id) if submission and submission.draft_id else None
        if not submission or not result:
            raise ServiceException("Assessment source data is unavailable.")
        facts: list[dict[str, Any]] = []
        chunks: list[DocumentChunkEntity] = []
        if draft:
            cipher = DocumentCipher()
            for fact in draft_repo.list_document_facts(draft.id)[:20]:
                try:
                    facts.append({
                        "label": fact.label,
                        "category": fact.category,
                        "value": cipher.decrypt_text(fact.encrypted_value, fact.value_encryption_nonce, str(draft.id).encode()),
                    })
                except Exception:
                    logger.warning("Skipping unreadable extracted fact id=%s", fact.id)
            try:
                embeddings = DocumentIntelligenceService()._embed(self.RETRIEVAL_QUERIES)
                deduped: dict[int, DocumentChunkEntity] = {}
                for embedding in embeddings:
                    for chunk in draft_repo.search_chunks(draft.id, embedding, limit=3):
                        deduped[chunk.id] = chunk
                chunks = list(deduped.values())[:12]
            except Exception:
                logger.exception("Traditional advisor retrieval failed; continuing with structured evidence only.")
        document_names = {document.id: document.filename for document in (draft_repo.list_documents(draft.id) if draft else [])}
        page_map = {page.id: page.page_number for page in db.scalars(select(DocumentPageEntity).where(DocumentPageEntity.id.in_([chunk.page_id for chunk in chunks] if chunks else [-1])))}
        cipher = DocumentCipher()
        allowed: dict[int, dict[str, Any]] = {}
        evidence_chunks: list[dict[str, Any]] = []
        for chunk in chunks:
            try:
                excerpt = cipher.decrypt_text(chunk.encrypted_text, chunk.encryption_nonce, str(chunk.draft_id).encode())[:800]
            except Exception:
                continue
            allowed[chunk.id] = {"document_id": chunk.document_id, "filename": document_names.get(chunk.document_id, "Uploaded document"), "page_number": page_map.get(chunk.page_id), "excerpt": excerpt}
            evidence_chunks.append({"chunk_id": chunk.id, **allowed[chunk.id]})
        answers = [{"question_key": answer.question_key, "construct": answer.construct, "value": answer.value} for answer in repo.get_answers_by_submission_id(submission.id)]
        confirmed = []
        if draft:
            for answer in draft_repo.list_evidence_answers(draft.id):
                if answer.evidence_status == "confirmed" and answer.final_value:
                    confirmed.append({"question_key": answer.question_key, "value": answer.final_value})
        return ({
            "profile": {key: getattr(submission, key) for key in ("industry", "org_size", "project_name", "project_type", "duration", "team_size", "budget")},
            "scores": {"agile": result.agile_score, "traditional": result.traditional_score, "flexibility": result.flexibility_score, "performance": result.performance_score, "strictness": result.strictness_score},
            "questionnaire_answers": answers,
            "confirmed_document_answers": confirmed,
            "extracted_facts": facts,
            "retrieved_chunks": evidence_chunks,
        }, allowed)

    def _generate(self, context: dict[str, Any]) -> dict[str, Any]:
        from google.genai import types
        client = DocumentIntelligenceService()._client()
        schema = {
            "type": "object", "properties": {
                "recommended_method": {"type": "string", "enum": list(self.METHODS)},
                "recommendation_summary": {"type": "string"}, "rationale": {"type": "string"},
                "alternatives": {"type": "array", "items": {"type": "object", "properties": {"method": {"type": "string", "enum": list(self.METHODS)}, "reason": {"type": "string"}}, "required": ["method", "reason"]}},
                "rollout": {"type": "array", "items": {"type": "object", "properties": {"phase": {"type": "string"}, "objective": {"type": "string"}, "actions": {"type": "array", "items": {"type": "string"}}, "control_artifacts": {"type": "array", "items": {"type": "string"}}}, "required": ["phase", "objective", "actions", "control_artifacts"]}},
                "tradeoffs": {"type": "array", "items": {"type": "string"}}, "evidence": {"type": "array", "items": {"type": "object", "properties": {"claim": {"type": "string"}, "chunk_ids": {"type": "array", "items": {"type": "integer"}}}, "required": ["claim", "chunk_ids"]}}, "limitations": {"type": "array", "items": {"type": "string"}}
            }, "required": ["recommended_method", "recommendation_summary", "rationale", "alternatives", "rollout", "tradeoffs", "evidence", "limitations"]
        }
        prompt = (
            "You are a project delivery advisor. The deterministic assessment already selected Traditional; do not revisit that decision. "
            "Choose exactly one method from the catalogue and two distinct alternatives. Use only the supplied assessment data. "
            "Cite retrieved document chunks only by chunk_ids. If no document chunks support a claim, use an empty list and state the limitation. "
            "Give exactly three practical rollout phases. Do not claim compliance or facts not in the context.\n"
            f"Catalogue: {json.dumps(self.METHODS)}\nContext: {json.dumps(context)}"
        )
        GeminiRequestLimiter().wait_for_slot("traditional_advisor")
        response = client.models.generate_content(model=settings.gemini_generation_model, contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema))
        return json.loads(getattr(response, "text", "") or "{}")

    def _validate(self, raw: dict[str, Any], allowed: dict[int, dict[str, Any]], has_documents: bool) -> TraditionalAdvisorPayload:
        primary = raw.get("recommended_method")
        alternatives = raw.get("alternatives") or []
        if primary not in self.METHODS or len(alternatives) != 2:
            raise ValidationException("Advisor returned an invalid methodology selection.")
        alternative_names = [item.get("method") for item in alternatives if isinstance(item, dict)]
        if any(name not in self.METHODS for name in alternative_names) or primary in alternative_names or len(set(alternative_names)) != 2:
            raise ValidationException("Advisor returned duplicate or unsupported alternatives.")
        citations = []
        for item in raw.get("evidence") or []:
            if not isinstance(item, dict) or not item.get("claim"):
                continue
            cited = []
            for chunk_id in item.get("chunk_ids") or []:
                try:
                    source = allowed.get(int(chunk_id))
                except (TypeError, ValueError):
                    source = None
                if source:
                    cited.append({**source, "claim": str(item["claim"])[:500]})
            citations.append({"claim": str(item["claim"])[:500], "citations": cited})
        limitations = [str(value)[:400] for value in raw.get("limitations") or []]
        if not has_documents:
            limitations.append("This recommendation is based on questionnaire answers; no supporting documents were available.")
        return TraditionalAdvisorPayload.model_validate({
            "recommended_method": primary, "recommendation_summary": str(raw.get("recommendation_summary", ""))[:1200], "rationale": str(raw.get("rationale", ""))[:2000],
            "alternatives": alternatives, "rollout": raw.get("rollout") or [], "tradeoffs": [str(value)[:500] for value in raw.get("tradeoffs") or []],
            "evidence": citations, "limitations": list(dict.fromkeys(limitations)),
        })

    def process_next_job(self, db: Session) -> bool:
        entity = db.scalar(select(TraditionalAdvisorEntity).where(TraditionalAdvisorEntity.status == "queued").order_by(TraditionalAdvisorEntity.created_at).with_for_update(skip_locked=True).limit(1))
        if not entity:
            return False
        entity.status, entity.attempts, entity.started_at = "running", entity.attempts + 1, datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        try:
            context, allowed = self._context(db, entity)
            payload = self._validate(self._generate(context), allowed, bool(context["retrieved_chunks"]))
            repo = AssessmentRepository(db)
            submission = repo.get_submission_by_id(entity.submission_id)
            draft = repo.get_draft_by_id(submission.draft_id) if submission and submission.draft_id else None
            ciphertext, nonce = DocumentCipher().encrypt_text(payload.model_dump_json(), self._aad(submission, draft))
            entity.status, entity.model_name = "ready", settings.gemini_generation_model
            entity.encrypted_payload, entity.encryption_nonce = ciphertext, nonce
            entity.error_code = entity.error_message = None
            entity.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.add(entity); db.commit()
        except Exception as exc:
            logger.exception("Traditional advisor failed id=%s", entity.id)
            entity.error_code = "GENERATION_FAILED"
            entity.error_message = "The methodology advisory could not be generated."
            entity.status = "queued" if entity.attempts < settings.traditional_advisor_retry_limit else "failed"
            db.add(entity); db.commit()
        return True
