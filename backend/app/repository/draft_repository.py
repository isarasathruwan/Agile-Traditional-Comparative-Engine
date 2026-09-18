from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.entity.assessment_entity import AssessmentSessionEntity
from app.entity.draft_entity import AssessmentDocumentEntity, AssessmentDraftEntity
from app.entity.document_intelligence_entity import (
    DocumentAgentRunEntity,
    DocumentChunkEntity,
    DocumentExtractedFactEntity,
    DocumentPageEntity,
    DocumentProcessingJobEntity,
    EvidenceAnswerEntity,
    EvidenceCitationEntity,
)
from app.repository.document_job_lock import acquire_document_job_lock


class DraftRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_draft(self, draft: AssessmentDraftEntity) -> AssessmentDraftEntity:
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def get_by_session_id(self, session_id: str) -> AssessmentDraftEntity | None:
        return self.db.scalar(
            select(AssessmentDraftEntity).where(AssessmentDraftEntity.session_id == session_id)
        )

    def get_draft(self, draft_id: int) -> AssessmentDraftEntity | None:
        return self.db.get(AssessmentDraftEntity, draft_id)

    def count_documents(self, draft_id: int) -> int:
        return self.db.scalar(
            select(func.count(AssessmentDocumentEntity.id)).where(AssessmentDocumentEntity.draft_id == draft_id)
        ) or 0

    def list_documents(self, draft_id: int) -> list[AssessmentDocumentEntity]:
        return list(
            self.db.scalars(
                select(AssessmentDocumentEntity)
                .where(AssessmentDocumentEntity.draft_id == draft_id)
                .order_by(AssessmentDocumentEntity.created_at.asc())
            )
        )

    def mark_transient_documents_failed(self, draft_id: int) -> None:
        """Stage terminal document status updates for the job transaction."""
        for document in self.list_documents(draft_id):
            if document.status in {"uploaded", "queued", "extracting", "embedding"}:
                document.status = "failed"
                self.db.add(document)

    def get_document_by_hash(self, draft_id: int, content_hash: str) -> AssessmentDocumentEntity | None:
        return self.db.scalar(
            select(AssessmentDocumentEntity).where(
                AssessmentDocumentEntity.draft_id == draft_id,
                AssessmentDocumentEntity.content_hash == content_hash,
            )
        )

    def create_document(self, document: AssessmentDocumentEntity) -> AssessmentDocumentEntity:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document: AssessmentDocumentEntity) -> None:
        self.db.delete(document)
        self.db.commit()

    def get_document(self, document_id: int) -> AssessmentDocumentEntity | None:
        return self.db.get(AssessmentDocumentEntity, document_id)

    def create_job(self, job: DocumentProcessingJobEntity) -> DocumentProcessingJobEntity:
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def has_active_job(self, draft_id: int) -> bool:
        return bool(
            self.db.scalar(
                select(DocumentProcessingJobEntity.id).where(
                    DocumentProcessingJobEntity.draft_id == draft_id,
                    DocumentProcessingJobEntity.status.in_(("queued", "extracting", "embedding", "reasoning")),
                )
            )
        )

    def supersede_queued_jobs(self, draft_id: int, excluded_job_id: int) -> None:
        self.db.query(DocumentProcessingJobEntity).filter(
            DocumentProcessingJobEntity.draft_id == draft_id,
            DocumentProcessingJobEntity.id != excluded_job_id,
            DocumentProcessingJobEntity.status == "queued",
        ).update(
            {
                DocumentProcessingJobEntity.status: "ready",
                DocumentProcessingJobEntity.error_code: "SUPERSEDED_BY_BATCH",
                DocumentProcessingJobEntity.error_message: "Superseded by a draft-level batch job.",
            },
            synchronize_session=False,
        )
        self.db.commit()

    def get_jobs_for_draft(self, draft_id: int) -> list[DocumentProcessingJobEntity]:
        return list(
            self.db.scalars(
                select(DocumentProcessingJobEntity)
                .where(DocumentProcessingJobEntity.draft_id == draft_id)
                .order_by(DocumentProcessingJobEntity.created_at.asc())
            )
        )

    def claim_next_job(self) -> DocumentProcessingJobEntity | None:
        job = self.db.scalar(
            select(DocumentProcessingJobEntity)
            .where(DocumentProcessingJobEntity.status == "queued")
            .order_by(DocumentProcessingJobEntity.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job:
            job.status = "extracting"
            job.attempts += 1
            self.db.add(job)
            self.db.flush()
            acquire_document_job_lock(self.db, job.id)
            self.db.commit()
            self.db.refresh(job)
        return job

    def save_job(self, job: DocumentProcessingJobEntity) -> None:
        self.db.add(job)
        self.db.commit()

    def clear_document_content(self, document_id: int) -> None:
        page_ids = list(
            self.db.scalars(select(DocumentPageEntity.id).where(DocumentPageEntity.document_id == document_id))
        )
        if page_ids:
            self.db.query(DocumentChunkEntity).filter(DocumentChunkEntity.page_id.in_(page_ids)).delete(
                synchronize_session=False
            )
        self.db.query(DocumentPageEntity).filter(DocumentPageEntity.document_id == document_id).delete(
            synchronize_session=False
        )

    def add_page(self, page: DocumentPageEntity) -> DocumentPageEntity:
        self.db.add(page)
        self.db.flush()
        return page

    def add_chunk(self, chunk: DocumentChunkEntity) -> None:
        self.db.add(chunk)

    def list_chunks_for_draft(self, draft_id: int) -> list[DocumentChunkEntity]:
        return list(
            self.db.scalars(
                select(DocumentChunkEntity)
                .where(DocumentChunkEntity.draft_id == draft_id)
                .order_by(DocumentChunkEntity.document_id, DocumentChunkEntity.page_id, DocumentChunkEntity.chunk_index)
            )
        )

    def list_chunks_for_document(self, document_id: int) -> list[DocumentChunkEntity]:
        return list(
            self.db.scalars(
                select(DocumentChunkEntity)
                .where(DocumentChunkEntity.document_id == document_id)
                .order_by(DocumentChunkEntity.page_id, DocumentChunkEntity.chunk_index)
            )
        )

    def search_chunks(self, draft_id: int, embedding: list[float], limit: int = 8) -> list[DocumentChunkEntity]:
        return list(
            self.db.scalars(
                select(DocumentChunkEntity)
                .where(DocumentChunkEntity.draft_id == draft_id)
                .order_by(DocumentChunkEntity.embedding.cosine_distance(embedding))
                .limit(limit)
            )
        )

    def upsert_evidence_answer(self, answer: EvidenceAnswerEntity) -> EvidenceAnswerEntity:
        existing = self.db.scalar(
            select(EvidenceAnswerEntity).where(
                EvidenceAnswerEntity.draft_id == answer.draft_id,
                EvidenceAnswerEntity.question_key == answer.question_key,
            )
        )
        if existing:
            existing.answer_type = answer.answer_type
            existing.proposed_value = answer.proposed_value
            existing.confidence = answer.confidence
            existing.evidence_status = answer.evidence_status
            existing.final_value = None
            existing.final_source = None
            existing.confirmed_at = None
            self.db.flush()
            return existing
        self.db.add(answer)
        self.db.flush()
        return answer

    def clear_citations(self, evidence_answer_id: int) -> None:
        self.db.query(EvidenceCitationEntity).filter(
            EvidenceCitationEntity.evidence_answer_id == evidence_answer_id
        ).delete(synchronize_session=False)

    def add_citation(self, citation: EvidenceCitationEntity) -> None:
        self.db.add(citation)

    def list_evidence_answers(self, draft_id: int) -> list[EvidenceAnswerEntity]:
        return list(
            self.db.scalars(
                select(EvidenceAnswerEntity)
                .where(EvidenceAnswerEntity.draft_id == draft_id)
                .order_by(EvidenceAnswerEntity.question_key.asc())
            )
        )

    def get_evidence_answer(self, draft_id: int, question_key: str) -> EvidenceAnswerEntity | None:
        return self.db.scalar(
            select(EvidenceAnswerEntity).where(
                EvidenceAnswerEntity.draft_id == draft_id,
                EvidenceAnswerEntity.question_key == question_key,
            )
        )

    def clear_evidence_answers(self, draft_id: int) -> None:
        answer_ids = list(
            self.db.scalars(select(EvidenceAnswerEntity.id).where(EvidenceAnswerEntity.draft_id == draft_id))
        )
        if answer_ids:
            self.db.query(EvidenceCitationEntity).filter(
                EvidenceCitationEntity.evidence_answer_id.in_(answer_ids)
            ).delete(synchronize_session=False)
        self.db.query(EvidenceAnswerEntity).filter(EvidenceAnswerEntity.draft_id == draft_id).delete(
            synchronize_session=False
        )

    def list_citations(self, evidence_answer_id: int) -> list[EvidenceCitationEntity]:
        return list(
            self.db.scalars(
                select(EvidenceCitationEntity)
                .where(EvidenceCitationEntity.evidence_answer_id == evidence_answer_id)
                .order_by(EvidenceCitationEntity.id.asc())
            )
        )

    def clear_document_facts(self, document_id: int) -> None:
        self.db.query(DocumentExtractedFactEntity).filter(
            DocumentExtractedFactEntity.document_id == document_id
        ).delete(synchronize_session=False)

    def add_document_fact(self, fact: DocumentExtractedFactEntity) -> None:
        self.db.add(fact)

    def list_document_facts(self, draft_id: int) -> list[DocumentExtractedFactEntity]:
        return list(
            self.db.scalars(
                select(DocumentExtractedFactEntity)
                .where(DocumentExtractedFactEntity.draft_id == draft_id)
                .order_by(
                    DocumentExtractedFactEntity.document_id,
                    DocumentExtractedFactEntity.category,
                    DocumentExtractedFactEntity.id,
                )
            )
        )

    def add_agent_run(self, run: DocumentAgentRunEntity) -> None:
        self.db.add(run)

    def save_draft(self, draft: AssessmentDraftEntity) -> AssessmentDraftEntity:
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def get_assessment_session(self, session_id: str) -> AssessmentSessionEntity | None:
        return self.db.scalar(
            select(AssessmentSessionEntity).where(AssessmentSessionEntity.session_id == session_id)
        )

    def save_assessment_session(self, session: AssessmentSessionEntity) -> AssessmentSessionEntity:
        self.db.add(session)
        self.db.flush()
        return session
