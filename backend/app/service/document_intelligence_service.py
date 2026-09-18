from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.config.config import settings
from app.entity.document_intelligence_entity import (
    DocumentAgentRunEntity,
    DocumentChunkEntity,
    DocumentExtractedFactEntity,
    DocumentPageEntity,
    DocumentProcessingJobEntity,
    EvidenceAnswerEntity,
    EvidenceCitationEntity,
)
from app.exceptions.domain_exception import NotFoundException, ServiceException, ValidationException
from app.model.draft_model import (
    DocumentExtractedFactData,
    EvidenceAnswerData,
    EvidenceCitationData,
    EvidenceAnswerUpdateRequest,
)
from app.model.questionnaire_model import DocumentExtractionConfig, DocumentQuestion, LikertQuestion, ProfileQuestion, QuestionnairePayload
from app.repository.draft_repository import DraftRepository
from app.repository.document_job_lock import release_document_job_lock
from app.util.encryption import DocumentCipher
from app.util.response import GenericResponse
from app.service.gemini_rate_limiter import GeminiRequestLimiter

logger = logging.getLogger(__name__)


class DocumentIntelligenceService:
    """Runs bounded, assessment-scoped retrieval and structured evidence extraction."""

    CHUNK_SIZE = 1_200
    CHUNK_OVERLAP = 180
    EMBEDDING_BATCH_SIZE = 64
    MAX_AGENT_ITERATIONS = 1
    FACT_CATEGORIES = {
        "project_context",
        "scope",
        "delivery_constraint",
        "dependency",
        "governance",
        "risk",
    }

    def _client(self):
        if not settings.gemini_api_key:
            raise ServiceException("Document processing is not configured. Set GEMINI_API_KEY to enable it.")
        from google import genai
        from google.genai import types

        return genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=settings.gemini_request_timeout_ms),
        )

    @staticmethod
    def _chunks(text: str) -> list[tuple[int, int, str]]:
        normalized = " ".join(text.split())
        if not normalized:
            return []
        chunks: list[tuple[int, int, str]] = []
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + DocumentIntelligenceService.CHUNK_SIZE)
            if end < len(normalized):
                boundary = normalized.rfind(" ", start, end)
                if boundary > start + 300:
                    end = boundary
            chunks.append((start, end, normalized[start:end]))
            if end == len(normalized):
                break
            start = max(end - DocumentIntelligenceService.CHUNK_OVERLAP, start + 1)
        return chunks

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._client()
        from google.genai import types

        values: list[list[float]] = []
        for start in range(0, len(texts), self.EMBEDDING_BATCH_SIZE):
            batch = texts[start : start + self.EMBEDDING_BATCH_SIZE]
            batch_number = (start // self.EMBEDDING_BATCH_SIZE) + 1
            total_batches = (len(texts) + self.EMBEDDING_BATCH_SIZE - 1) // self.EMBEDDING_BATCH_SIZE
            batch_started = time.monotonic()
            logger.info(
                "Document processing embedding request started batch=%s/%s chunks=%s",
                batch_number,
                total_batches,
                len(batch),
            )
            GeminiRequestLimiter().wait_for_slot("embedding")
            response = client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(output_dimensionality=settings.gemini_embedding_dimensions),
            )
            embeddings = getattr(response, "embeddings", [])
            if len(embeddings) != len(batch):
                raise ServiceException("Google AI returned an incomplete embedding response.")
            logger.info(
                "Document processing embedding request completed batch=%s/%s chunks=%s duration_ms=%s",
                batch_number,
                total_batches,
                len(batch),
                round((time.monotonic() - batch_started) * 1000),
            )
            for item in embeddings:
                item_values = getattr(item, "values", None)
                if item_values is None and isinstance(item, dict):
                    item_values = item.get("values")
                if not item_values:
                    raise ServiceException("Google AI returned an invalid embedding response.")
                values.append(list(item_values))
        if len(values) != len(texts):
            raise ServiceException("Google AI returned an incomplete embedding response.")
        return values

    def _read_document(self, draft_id: str, storage_path: str, nonce: str | None) -> bytes:
        if not nonce or storage_path == "mock_path":
            raise ValidationException("This document was uploaded before encrypted processing was enabled. Upload it again.")
        ciphertext = Path(storage_path).read_text(encoding="utf-8")
        return DocumentCipher().decrypt(ciphertext, nonce, draft_id.encode("utf-8"))

    @staticmethod
    def _extract_pages(document_bytes: bytes) -> list[tuple[int, str]]:
        try:
            reader = PdfReader(BytesIO(document_bytes))
        except Exception as exc:
            raise ValidationException("Unable to read the uploaded PDF.") from exc
        pages = [(index + 1, page.extract_text() or "") for index, page in enumerate(reader.pages)]
        if sum(len(text.strip()) for _, text in pages) < settings.pdf_min_extracted_characters:
            raise ValidationException("This PDF has no usable selectable text. Scanned PDFs are not supported yet.")
        return pages

    @staticmethod
    def _question_config(question: ProfileQuestion | LikertQuestion | DocumentQuestion) -> DocumentExtractionConfig:
        return question.document_extraction

    def _generate_candidate(
        self,
        question: ProfileQuestion | LikertQuestion | DocumentQuestion,
        config: DocumentExtractionConfig,
        chunks: list[DocumentChunkEntity],
        cipher: DocumentCipher,
    ) -> dict[str, Any] | None:
        context = []
        for chunk in chunks:
            text = cipher.decrypt_text(chunk.encrypted_text, chunk.encryption_nonce, str(chunk.draft_id).encode("utf-8"))
            context.append({"chunk_id": chunk.id, "page": None, "text": text})
        options = getattr(question, "options", None) or []
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "string", "enum": ["high", "moderate", "low", "none"]},
                "evidence_chunk_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["value", "confidence", "evidence_chunk_ids"],
        }
        prompt = (
            "You extract evidence from anonymized project documents. Use only the supplied chunks. "
            "Do not infer facts that are not directly supported. Return an empty value with confidence none when evidence is insufficient.\n"
            f"Question key: {question.question_id}\nQuestion: {question.prompt}\nInstruction: {config.instruction}\n"
            f"Answer type: {config.answer_type}\nAllowed options: {options}\nRubric: {config.rubric or 'none'}\n"
            f"Chunks: {json.dumps(context)}"
        )
        client = self._client()
        from google.genai import types

        logger.info("Document reasoning request started question=%s chunks=%s", question.question_id, len(chunks))
        request_started = time.monotonic()
        GeminiRequestLimiter().wait_for_slot("document_reasoning")
        response = client.models.generate_content(
            model=settings.gemini_generation_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema),
        )
        text = getattr(response, "text", "")
        logger.info(
            "Document reasoning request completed question=%s duration_ms=%s has_response=%s",
            question.question_id,
            round((time.monotonic() - request_started) * 1000),
            bool(text),
        )
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _generate_document_facts(
        self, document_name: str, chunks: list[DocumentChunkEntity], cipher: DocumentCipher
    ) -> list[dict[str, Any]]:
        """Extract only concrete, source-addressable facts from one document."""
        context = []
        for chunk in chunks[:16]:
            context.append(
                {
                    "chunk_id": chunk.id,
                    "text": cipher.decrypt_text(
                        chunk.encrypted_text,
                        chunk.encryption_nonce,
                        str(chunk.draft_id).encode("utf-8"),
                    ),
                }
            )
        if not context:
            return []
        schema = {
            "type": "object",
            "properties": {
                "facts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                            "confidence": {"type": "string", "enum": ["high", "moderate", "low"]},
                            "source_chunk_id": {"type": "integer"},
                        },
                        "required": ["category", "label", "value", "confidence", "source_chunk_id"],
                    },
                }
            },
            "required": ["facts"],
        }
        prompt = (
            "Extract concise, factual project observations from the supplied document chunks. "
            "Use only statements directly supported by one supplied chunk. Do not infer, score, recommend, "
            "or duplicate the same fact. Prefer project context, scope, delivery constraints, dependencies, "
            "governance, and risks. Use one of these categories exactly: "
            "project_context, scope, delivery_constraint, dependency, governance, risk. Return at most 10 facts.\n"
            f"Document: {document_name}\nChunks: {json.dumps(context)}"
        )
        client = self._client()
        from google.genai import types

        logger.info("Document fact extraction request started document=%s chunks=%s", document_name, len(context))
        request_started = time.monotonic()
        GeminiRequestLimiter().wait_for_slot("document_fact_extraction")
        response = client.models.generate_content(
            model=settings.gemini_generation_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema),
        )
        logger.info(
            "Document fact extraction request completed document=%s duration_ms=%s",
            document_name,
            round((time.monotonic() - request_started) * 1000),
        )
        try:
            payload = json.loads(getattr(response, "text", "") or "{}")
        except json.JSONDecodeError:
            return []
        facts = payload.get("facts")
        return facts if isinstance(facts, list) else []

    def _run_document_fact_agent(
        self,
        db: Session,
        repository: DraftRepository,
        draft_id: int,
        document_id: int,
        document_name: str,
    ) -> None:
        """Persist encrypted fact records. Fact extraction is advisory, never blocking."""
        started = time.monotonic()
        cipher = DocumentCipher()
        logger.info("Document fact extraction started draft_id=%s document_id=%s", draft_id, document_id)
        facts = self._generate_document_facts(
            document_name,
            repository.list_chunks_for_document(document_id),
            cipher,
        )
        chunks = {chunk.id: chunk for chunk in repository.list_chunks_for_document(document_id)}
        repository.clear_document_facts(document_id)
        stored = 0
        for item in facts[:10]:
            try:
                category = str(item.get("category") or "").strip().lower()
                label = str(item.get("label") or "").strip()
                value = str(item.get("value") or "").strip()
                chunk = chunks.get(int(item.get("source_chunk_id")))
            except (TypeError, ValueError):
                continue
            if category not in self.FACT_CATEGORIES or not label or not value or not chunk:
                continue
            encrypted_value, value_nonce = cipher.encrypt_text(value[:1_000], str(draft_id).encode("utf-8"))
            excerpt = cipher.decrypt_text(
                chunk.encrypted_text,
                chunk.encryption_nonce,
                str(chunk.draft_id).encode("utf-8"),
            )[:500]
            encrypted_excerpt, excerpt_nonce = cipher.encrypt_text(excerpt, str(draft_id).encode("utf-8"))
            repository.add_document_fact(
                DocumentExtractedFactEntity(
                    draft_id=draft_id,
                    document_id=document_id,
                    source_chunk_id=chunk.id,
                    category=category,
                    label=label[:160],
                    encrypted_value=encrypted_value,
                    value_encryption_nonce=value_nonce,
                    encrypted_excerpt=encrypted_excerpt,
                    excerpt_encryption_nonce=excerpt_nonce,
                    confidence=str(item.get("confidence") or "moderate")[:20],
                )
            )
            stored += 1
        repository.add_agent_run(
            DocumentAgentRunEntity(
                draft_id=draft_id,
                question_key="document_facts",
                model_name=settings.gemini_generation_model,
                status="completed" if stored else "no_evidence",
                trace_json={"document_id": document_id, "facts_stored": stored},
                duration_ms=round((time.monotonic() - started) * 1000),
            )
        )
        db.commit()
        logger.info(
            "Document fact extraction completed draft_id=%s document_id=%s facts_stored=%s duration_ms=%s",
            draft_id,
            document_id,
            stored,
            round((time.monotonic() - started) * 1000),
        )

    @staticmethod
    def _valid_value(question: ProfileQuestion | LikertQuestion | DocumentQuestion, value: str | None) -> bool:
        if value is None:
            return False
        config = question.document_extraction
        if config.answer_type == "likert":
            return value.strip() in {"1", "2", "3", "4", "5"}
        options = getattr(question, "options", None) or []
        return not options or value in options

    @staticmethod
    def _candidate_chunk_ids(candidate: dict[str, Any] | None) -> set[int]:
        """Normalize JSON schema-compatible chunk identifiers returned by an LLM."""
        raw_ids = (candidate or {}).get("evidence_chunk_ids", [])
        if not isinstance(raw_ids, list):
            return set()
        chunk_ids: set[int] = set()
        for raw_id in raw_ids:
            if isinstance(raw_id, int) and not isinstance(raw_id, bool) and raw_id > 0:
                chunk_ids.add(raw_id)
            elif isinstance(raw_id, str) and raw_id.strip().isdigit():
                parsed_id = int(raw_id.strip())
                if parsed_id > 0:
                    chunk_ids.add(parsed_id)
        return chunk_ids

    def _store_proposal(
        self,
        repository: DraftRepository,
        draft_id: int,
        question: ProfileQuestion | LikertQuestion | DocumentQuestion,
        candidate: dict[str, Any] | None,
        retrieved: list[DocumentChunkEntity],
        cipher: DocumentCipher,
    ) -> None:
        config = question.document_extraction
        requested_ids = self._candidate_chunk_ids(candidate)
        selected = [chunk for chunk in retrieved if chunk.id in requested_ids]
        value = str((candidate or {}).get("value") or "").strip() or None
        valid = bool(
            selected
            and self._valid_value(question, value)
            and str((candidate or {}).get("confidence") or "none") in {"high", "moderate"}
        )
        if valid:
            proposed_value = value
            confidence = str((candidate or {}).get("confidence") or "moderate")
            status = "suggested"
        elif config.answer_type == "likert":
            proposed_value = "3"
            confidence = "none"
            status = "no_evidence"
        else:
            proposed_value = None
            confidence = "none"
            status = "needs_input"

        answer = repository.upsert_evidence_answer(
            EvidenceAnswerEntity(
                draft_id=draft_id,
                question_key=question.question_id,
                answer_type=config.answer_type,
                proposed_value=proposed_value,
                confidence=confidence,
                evidence_status=status,
            )
        )
        repository.clear_citations(answer.id)
        for chunk in selected[:3]:
            excerpt = cipher.decrypt_text(chunk.encrypted_text, chunk.encryption_nonce, str(chunk.draft_id).encode("utf-8"))[:500]
            encrypted_excerpt, nonce = cipher.encrypt_text(excerpt, str(draft_id).encode("utf-8"))
            repository.add_citation(
                EvidenceCitationEntity(
                    evidence_answer_id=answer.id,
                    chunk_id=chunk.id,
                    page_number=0,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    encrypted_excerpt=encrypted_excerpt,
                    encryption_nonce=nonce,
                )
            )

    def _run_question_agent(
        self,
        db: Session,
        repository: DraftRepository,
        draft_id: int,
        question: ProfileQuestion | LikertQuestion | DocumentQuestion,
        query: str | None = None,
        query_embedding: list[float] | None = None,
    ) -> None:
        started = time.monotonic()
        cipher = DocumentCipher()
        queries: list[str] = []
        candidate: dict[str, Any] | None = None
        retrieved: list[DocumentChunkEntity] = []
        for attempt in range(1, self.MAX_AGENT_ITERATIONS + 1):
            logger.info(
                "Document reasoning iteration started draft_id=%s question=%s attempt=%s/%s",
                draft_id,
                question.question_id,
                attempt,
                self.MAX_AGENT_ITERATIONS,
            )
            current_query = query or f"task: question answering | query: {question.prompt} | attempt {attempt}"
            queries.append(current_query)
            current_embedding = query_embedding if attempt == 1 and query_embedding is not None else self._embed([current_query])[0]
            retrieved = repository.search_chunks(draft_id, current_embedding)
            if not retrieved:
                break
            candidate = self._generate_candidate(question, question.document_extraction, retrieved, cipher)
            if candidate and candidate.get("value") and candidate.get("evidence_chunk_ids"):
                break
        self._store_proposal(repository, draft_id, question, candidate, retrieved, cipher)
        repository.add_agent_run(
            DocumentAgentRunEntity(
                draft_id=draft_id,
                question_key=question.question_id,
                model_name=settings.gemini_generation_model,
                status="completed" if candidate else "no_evidence",
                trace_json={
                    "iterations": len(queries),
                    "queries": queries,
                    "retrieved_chunk_ids": [chunk.id for chunk in retrieved],
                    "candidate_valid": bool(candidate and candidate.get("value")),
                },
                duration_ms=round((time.monotonic() - started) * 1000),
            )
        )
        db.commit()
        logger.info(
            "Document reasoning question completed draft_id=%s question=%s iterations=%s retrieved_chunks=%s duration_ms=%s",
            draft_id,
            question.question_id,
            len(queries),
            len(retrieved),
            round((time.monotonic() - started) * 1000),
        )

    def process_next_job(self, db: Session) -> bool:
        repository = DraftRepository(db)
        job = repository.claim_next_job()
        if not job:
            return False
        started = datetime.utcnow()
        processing_started = time.monotonic()
        try:
            draft = repository.get_draft(job.draft_id)
            if not draft:
                raise NotFoundException("Document processing context was not found.")
            # Older per-document jobs are upgraded to the same full-corpus behavior.
            repository.supersede_queued_jobs(draft.id, job.id)
            documents = repository.list_documents(draft.id)
            if not documents:
                raise ValidationException("No uploaded documents are available for processing.")
            logger.info(
                "Document processing job started job_id=%s draft_id=%s documents=%s attempt=%s",
                job.id,
                draft.id,
                len(documents),
                job.attempts,
            )
            job.started_at = started
            job.status = "extracting"
            repository.save_job(job)

            documents_to_index = [
                document
                for document in documents
                if document.status in {"uploaded", "queued", "extracting", "embedding"}
            ]
            pending_chunks: list[tuple[object, DocumentPageEntity, int, int, int, str]] = []
            indexed_documents = []
            cipher = DocumentCipher()
            for document in documents_to_index:
                document_started = time.monotonic()
                logger.info(
                    "Document extraction started job_id=%s document_id=%s filename=%s",
                    job.id,
                    document.id,
                    document.filename,
                )
                document.status = "extracting"
                db.add(document)
                try:
                    raw = self._read_document(draft.session_id, document.storage_path, document.encryption_nonce)
                    pages = self._extract_pages(raw)
                    repository.clear_document_content(document.id)
                    repository.clear_document_facts(document.id)
                    for page_number, text in pages:
                        if not text.strip():
                            continue
                        encrypted_text, nonce = cipher.encrypt_text(text, draft.session_id.encode("utf-8"))
                        page = repository.add_page(
                            DocumentPageEntity(
                                document_id=document.id,
                                page_number=page_number,
                                encrypted_text=encrypted_text,
                                encryption_nonce=nonce,
                                character_count=len(text),
                            )
                        )
                        for chunk_index, (char_start, char_end, chunk_text) in enumerate(self._chunks(text)):
                            pending_chunks.append((document, page, chunk_index, char_start, char_end, chunk_text))
                    document.status = "embedding"
                    indexed_documents.append(document)
                    document_chunks = sum(1 for item in pending_chunks if item[0].id == document.id)
                    logger.info(
                        "Document extraction completed job_id=%s document_id=%s pages=%s chunks=%s duration_ms=%s",
                        job.id,
                        document.id,
                        len(pages),
                        document_chunks,
                        round((time.monotonic() - document_started) * 1000),
                    )
                except ValidationException as exc:
                    document.status = "unsupported"
                    db.add(
                        DocumentAgentRunEntity(
                            draft_id=draft.id,
                            question_key="document_processing",
                            model_name="local_pdf_reader",
                            status="unsupported",
                            trace_json={"document_id": document.id, "error": str(exc)},
                            duration_ms=0,
                        )
                    )
                    logger.info("Document skipped during batch processing document_id=%s error=%s", document.id, exc)

            job.status = "embedding"
            db.add(job)
            db.commit()

            if not indexed_documents:
                job.status = "failed"
                job.error_code = "NO_USABLE_DOCUMENTS"
                job.error_message = "None of the uploaded PDFs contained usable selectable text."
                job.completed_at = datetime.utcnow()
                draft.status = "failed"
                db.add_all([job, draft])
                db.commit()
                return True

            logger.info(
                "Document embedding started job_id=%s draft_id=%s chunks=%s",
                job.id,
                draft.id,
                len(pending_chunks),
            )
            embeddings = self._embed(
                [f"title: {document.filename} | text: {chunk_text}" for document, _, _, _, _, chunk_text in pending_chunks]
            )
            for item, embedding in zip(pending_chunks, embeddings, strict=True):
                document, page, chunk_index, char_start, char_end, chunk_text = item
                encrypted_text, nonce = cipher.encrypt_text(chunk_text, str(draft.id).encode("utf-8"))
                repository.add_chunk(
                    DocumentChunkEntity(
                        draft_id=draft.id,
                        document_id=document.id,
                        page_id=page.id,
                        chunk_index=chunk_index,
                        char_start=char_start,
                        char_end=char_end,
                        encrypted_text=encrypted_text,
                        encryption_nonce=nonce,
                        embedding=embedding,
                    )
                )
            db.commit()
            logger.info(
                "Document embedding completed job_id=%s draft_id=%s chunks=%s",
                job.id,
                draft.id,
                len(pending_chunks),
            )

            # Facts are generated only after the entire valid document set is indexed.
            fact_documents = [
                document for document in repository.list_documents(draft.id) if document.status in {"embedding", "processed"}
            ]
            try:
                for document in fact_documents:
                    self._run_document_fact_agent(db, repository, draft.id, document.id, document.filename)
            except Exception:
                # Facts enrich the participant result but must never block evidence retrieval.
                db.rollback()
                logger.exception("Document fact extraction failed draft_id=%s", draft.id)

            job.status = "reasoning"
            job.completed_at = None
            db.add(job)
            db.commit()
            questionnaire = QuestionnairePayload.model_validate_json(draft.questionnaire_snapshot or "{}")
            logger.info(
                "Document reasoning started job_id=%s draft_id=%s questions=%s",
                job.id,
                draft.id,
                len(questionnaire.document_questions),
            )
            repository.clear_evidence_answers(draft.id)
            questions = questionnaire.document_questions
            retrieval_queries = [f"task: question answering | query: {question.prompt}" for question in questions]
            retrieval_embeddings = self._embed(retrieval_queries) if retrieval_queries else []
            for question_index, (question, query, query_embedding) in enumerate(
                zip(questions, retrieval_queries, retrieval_embeddings, strict=True), start=1
            ):
                logger.info(
                    "Document reasoning question started job_id=%s question=%s progress=%s/%s",
                    job.id,
                    question.question_id,
                    question_index,
                    len(questionnaire.document_questions),
                )
                self._run_question_agent(
                    db,
                    repository,
                    draft.id,
                    question,
                    query=query,
                    query_embedding=query_embedding,
                )
            for document in indexed_documents:
                document.status = "processed"
                db.add(document)
            job.status = "ready"
            job.completed_at = datetime.utcnow()
            draft.status = "ready"
            db.add_all([job, draft])
            db.commit()
            logger.info(
                "Document processing job completed job_id=%s draft_id=%s duration_ms=%s",
                job.id,
                draft.id,
                round((time.monotonic() - processing_started) * 1000),
            )
            return True
        except Exception as exc:
            db.rollback()
            job = db.get(DocumentProcessingJobEntity, job.id)
            if job:
                job.error_code = "PROCESSING_ERROR"
                job.error_message = str(exc)[:500]
                if job.attempts < settings.document_worker_retry_limit:
                    job.status = "queued"
                else:
                    job.status = "failed"
                    job.completed_at = datetime.utcnow()
                    draft = repository.get_draft(job.draft_id)
                    if draft:
                        draft.status = "failed"
                        db.add(draft)
                    repository.mark_transient_documents_failed(job.draft_id)
                repository.save_job(job)
            logger.exception(
                "Document processing job failed job_id=%s duration_ms=%s",
                job.id if job else "unknown",
                round((time.monotonic() - processing_started) * 1000),
            )
            return True
        finally:
            try:
                release_document_job_lock(db, job.id)
            except Exception:
                db.rollback()
                logger.exception("Document processing lock release failed job_id=%s", job.id)

    def list_evidence_answers(self, db: Session, draft_id: str) -> GenericResponse[list[EvidenceAnswerData]]:
        repository = DraftRepository(db)
        draft = repository.get_by_session_id(draft_id)
        if not draft:
            raise NotFoundException("Draft not found")
        questionnaire = (
            QuestionnairePayload.model_validate_json(draft.questionnaire_snapshot)
            if draft.questionnaire_snapshot
            else None
        )
        document_questions = {item.question_id: item for item in questionnaire.document_questions} if questionnaire else {}
        cipher = DocumentCipher()
        items: list[EvidenceAnswerData] = []
        for answer in repository.list_evidence_answers(draft.id):
            citations: list[EvidenceCitationData] = []
            for citation in repository.list_citations(answer.id):
                chunk = db.get(DocumentChunkEntity, citation.chunk_id)
                document = repository.get_document(chunk.document_id) if chunk else None
                if not chunk or not document:
                    continue
                citations.append(
                    EvidenceCitationData(
                        document_id=document.id,
                        filename=document.filename,
                        page_number=self._page_number(db, chunk.page_id),
                        excerpt=cipher.decrypt_text(citation.encrypted_excerpt, citation.encryption_nonce, str(draft.id).encode("utf-8")),
                    )
                )
            items.append(
                EvidenceAnswerData(
                    question_key=answer.question_key,
                    prompt=document_questions.get(answer.question_key).prompt if answer.question_key in document_questions else None,
                    construct_key=(
                        document_questions[answer.question_key].construct_key
                        if answer.question_key in document_questions
                        else None
                    ),
                    weight=document_questions[answer.question_key].weight if answer.question_key in document_questions else None,
                    answer_type=answer.answer_type,
                    proposed_value=answer.proposed_value,
                    confidence=answer.confidence,
                    evidence_status=answer.evidence_status,
                    final_value=answer.final_value,
                    final_source=answer.final_source,
                    citations=citations,
                )
            )
        return GenericResponse.success_response("Evidence answers fetched.", data=items)

    def list_document_facts(self, db: Session, draft_id: str) -> GenericResponse[list[DocumentExtractedFactData]]:
        repository = DraftRepository(db)
        draft = repository.get_by_session_id(draft_id)
        if not draft:
            raise NotFoundException("Draft not found")
        cipher = DocumentCipher()
        items: list[DocumentExtractedFactData] = []
        for fact in repository.list_document_facts(draft.id):
            document = repository.get_document(fact.document_id)
            chunk = db.get(DocumentChunkEntity, fact.source_chunk_id)
            if not document or not chunk:
                continue
            items.append(
                DocumentExtractedFactData(
                    id=fact.id,
                    document_id=document.id,
                    filename=document.filename,
                    category=fact.category,
                    label=fact.label,
                    value=cipher.decrypt_text(
                        fact.encrypted_value,
                        fact.value_encryption_nonce,
                        str(draft.id).encode("utf-8"),
                    ),
                    confidence=fact.confidence,
                    page_number=self._page_number(db, chunk.page_id),
                    excerpt=cipher.decrypt_text(
                        fact.encrypted_excerpt,
                        fact.excerpt_encryption_nonce,
                        str(draft.id).encode("utf-8"),
                    ),
                )
            )
        return GenericResponse.success_response("Document facts fetched.", data=items)

    @staticmethod
    def _page_number(db: Session, page_id: int) -> int:
        page = db.get(DocumentPageEntity, page_id)
        return page.page_number if page else 0

    def confirm_evidence_answer(
        self, db: Session, draft_id: str, question_key: str, payload: EvidenceAnswerUpdateRequest
    ) -> GenericResponse[EvidenceAnswerData]:
        repository = DraftRepository(db)
        draft = repository.get_by_session_id(draft_id)
        answer = repository.get_evidence_answer(draft.id, question_key) if draft else None
        if not draft or not answer:
            raise NotFoundException("Evidence answer not found.")
        questionnaire = (
            QuestionnairePayload.model_validate_json(draft.questionnaire_snapshot)
            if draft.questionnaire_snapshot
            else None
        )
        document_question_keys = {item.question_id for item in questionnaire.document_questions} if questionnaire else set()
        if answer.question_key not in document_question_keys:
            raise ValidationException("Only document-only evidence questions can be confirmed.")
        if payload.action == "omit":
            answer.final_value = None
            answer.final_source = "omitted_document"
            answer.evidence_status = "omitted"
        else:
            citations = repository.list_citations(answer.id)
            if (
                answer.answer_type != "likert"
                or answer.evidence_status != "suggested"
                or answer.confidence not in {"high", "moderate"}
                or not answer.proposed_value
                or not citations
            ):
                raise ValidationException("Only cited, moderate-or-high confidence document evidence can be confirmed.")
            answer.final_value = answer.proposed_value
            answer.final_source = "confirmed_document"
        answer.confirmed_at = datetime.utcnow()
        db.add(answer)
        db.commit()
        return GenericResponse.success_response(
            "Evidence answer confirmed.",
            data=EvidenceAnswerData(
                question_key=answer.question_key,
                prompt=next((item.prompt for item in (questionnaire.document_questions if questionnaire else []) if item.question_id == answer.question_key), None),
                construct_key=next((item.construct_key for item in (questionnaire.document_questions if questionnaire else []) if item.question_id == answer.question_key), None),
                weight=next((item.weight for item in (questionnaire.document_questions if questionnaire else []) if item.question_id == answer.question_key), None),
                answer_type=answer.answer_type,
                proposed_value=answer.proposed_value,
                confidence=answer.confidence,
                evidence_status=answer.evidence_status,
                final_value=answer.final_value,
                final_source=answer.final_source,
                citations=[],
            ),
        )
