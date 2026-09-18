import logging
from datetime import datetime

from sqlalchemy import case, delete, func, select
from sqlalchemy.orm import Session

from app.entity.assessment_entity import (
    AssessmentAnswerEntity,
    AssessmentResultEntity,
    AssessmentSessionEntity,
    AssessmentSubmissionEntity,
)
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
from app.entity.traditional_advisor_entity import TraditionalAdvisorEntity
from app.repository.document_job_lock import document_job_has_live_worker


logger = logging.getLogger(__name__)


class AssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_submission(self, payload: AssessmentSubmissionEntity) -> AssessmentSubmissionEntity:
        logger.debug("create_submission called for company=%s", payload.company)
        self.db.add(payload)
        self.db.flush()
        logger.info("Submission created id=%s", payload.id)
        return payload

    def create_answer(self, payload: AssessmentAnswerEntity) -> None:
        self.db.add(payload)

    def create_result(self, payload: AssessmentResultEntity) -> AssessmentResultEntity:
        self.db.add(payload)
        self.db.commit()
        self.db.refresh(payload)
        logger.info("Result created for submission_id=%s", payload.submission_id)
        return payload

    def get_result_by_submission_id(self, submission_id: int) -> AssessmentResultEntity | None:
        logger.debug("get_result_by_submission_id submission_id=%s", submission_id)
        return self.db.scalar(
            select(AssessmentResultEntity).where(AssessmentResultEntity.submission_id == submission_id)
        )

    def get_sessions_by_submission_id(self, submission_id: int) -> list[AssessmentSessionEntity]:
        return list(
            self.db.scalars(
                select(AssessmentSessionEntity).where(AssessmentSessionEntity.submission_id == submission_id)
            )
        )

    def get_submission_by_id(self, submission_id: int) -> AssessmentSubmissionEntity | None:
        logger.debug("get_submission_by_id submission_id=%s", submission_id)
        return self.db.scalar(
            select(AssessmentSubmissionEntity).where(AssessmentSubmissionEntity.id == submission_id)
        )

    def count_submissions_for_draft(self, draft_id: int) -> int:
        return self.db.scalar(
            select(func.count(AssessmentSubmissionEntity.id)).where(AssessmentSubmissionEntity.draft_id == draft_id)
        ) or 0

    def get_draft_by_id(self, draft_id: int) -> AssessmentDraftEntity | None:
        return self.db.scalar(select(AssessmentDraftEntity).where(AssessmentDraftEntity.id == draft_id))

    def get_answers_by_submission_id(self, submission_id: int) -> list[AssessmentAnswerEntity]:
        logger.debug("get_answers_by_submission_id submission_id=%s", submission_id)
        return list(
            self.db.scalars(
                select(AssessmentAnswerEntity)
                .where(AssessmentAnswerEntity.submission_id == submission_id)
                .order_by(AssessmentAnswerEntity.question_key.asc())
            )
        )

    def get_draft_by_session_id(self, draft_session_id: str) -> AssessmentDraftEntity | None:
        return self.db.scalar(
            select(AssessmentDraftEntity).where(AssessmentDraftEntity.session_id == draft_session_id)
        )

    def save_submission(self, submission: AssessmentSubmissionEntity) -> AssessmentSubmissionEntity:
        self.db.add(submission)
        self.db.flush()
        return submission

    def save_draft(self, draft: AssessmentDraftEntity) -> AssessmentDraftEntity:
        self.db.add(draft)
        self.db.flush()
        return draft

    def get_session_by_session_id(self, session_id: str) -> AssessmentSessionEntity | None:
        return self.db.scalar(select(AssessmentSessionEntity).where(AssessmentSessionEntity.session_id == session_id))

    def create_session(self, session: AssessmentSessionEntity) -> AssessmentSessionEntity:
        self.db.add(session)
        self.db.flush()
        return session

    def save_session(self, session: AssessmentSessionEntity) -> AssessmentSessionEntity:
        self.db.add(session)
        self.db.flush()
        return session

    def delete_assessment_bundle(self, submission_id: int) -> dict[str, object]:
        submission = self.get_submission_by_id(submission_id)
        if not submission:
            return {
                "deleted_documents": [],
                "deleted_session": False,
                "deleted_draft": False,
            }

        result = self.get_result_by_submission_id(submission_id)
        answers = self.get_answers_by_submission_id(submission_id)
        sessions = self.get_sessions_by_submission_id(submission_id)
        draft = self.get_draft_by_id(submission.draft_id) if submission.draft_id else None
        should_delete_draft = bool(
            draft and self.count_submissions_for_draft(int(draft.id)) <= 1
        )
        documents = self.list_documents_for_draft(int(draft.id)) if draft and should_delete_draft else []

        for answer in answers:
            self.db.delete(answer)
        self.db.query(TraditionalAdvisorEntity).filter(
            TraditionalAdvisorEntity.submission_id == submission_id
        ).delete(synchronize_session=False)
        if result:
            self.db.delete(result)
        for session in sessions:
            self.db.delete(session)
        for document in documents:
            self.db.delete(document)
        if draft and should_delete_draft:
            self.db.delete(draft)
        self.db.delete(submission)
        self.db.commit()
        logger.info(
            "Deleted assessment submission_id=%s draft_deleted=%s session_deleted=%s documents_deleted=%s",
            submission_id,
            should_delete_draft,
            bool(sessions),
            len(documents),
        )
        return {
            "deleted_documents": documents,
            "deleted_session": bool(sessions),
            "deleted_draft": should_delete_draft,
        }

    def get_incomplete_activity_snapshot(self, lock: bool = False) -> dict[str, object]:
        draft_query = select(AssessmentDraftEntity).where(
            ~select(AssessmentSubmissionEntity.id)
            .where(AssessmentSubmissionEntity.draft_id == AssessmentDraftEntity.id)
            .exists()
        )
        session_query = select(AssessmentSessionEntity).where(AssessmentSessionEntity.submission_id.is_(None))
        if lock:
            draft_query = draft_query.with_for_update()
            session_query = session_query.with_for_update()

        drafts = list(self.db.scalars(draft_query))
        sessions = list(self.db.scalars(session_query))
        draft_ids = [int(draft.id) for draft in drafts]
        documents = (
            list(
                self.db.scalars(
                    select(AssessmentDocumentEntity).where(AssessmentDocumentEntity.draft_id.in_(draft_ids))
                )
            )
            if draft_ids
            else []
        )
        job_query = select(DocumentProcessingJobEntity).where(
            DocumentProcessingJobEntity.draft_id.in_(draft_ids)
        )
        if lock:
            job_query = job_query.with_for_update()
        jobs = list(self.db.scalars(job_query)) if draft_ids else []

        evidence_records = 0
        if draft_ids:
            document_ids = [int(document.id) for document in documents]
            evidence_answer_ids = list(
                self.db.scalars(select(EvidenceAnswerEntity.id).where(EvidenceAnswerEntity.draft_id.in_(draft_ids)))
            )
            chunk_ids = list(
                self.db.scalars(select(DocumentChunkEntity.id).where(DocumentChunkEntity.draft_id.in_(draft_ids)))
            )
            if document_ids:
                evidence_records += int(
                    self.db.scalar(
                        select(func.count(DocumentPageEntity.id)).where(
                            DocumentPageEntity.document_id.in_(document_ids)
                        )
                    )
                    or 0
                )
            evidence_records += int(
                self.db.scalar(
                    select(func.count(DocumentChunkEntity.id)).where(DocumentChunkEntity.draft_id.in_(draft_ids))
                )
                or 0
            )
            evidence_records += int(
                self.db.scalar(
                    select(func.count(EvidenceAnswerEntity.id)).where(EvidenceAnswerEntity.draft_id.in_(draft_ids))
                )
                or 0
            )
            if evidence_answer_ids and chunk_ids:
                citation_filter = (
                    EvidenceCitationEntity.evidence_answer_id.in_(evidence_answer_ids)
                    | EvidenceCitationEntity.chunk_id.in_(chunk_ids)
                )
                evidence_records += int(
                    self.db.scalar(select(func.count(EvidenceCitationEntity.id)).where(citation_filter)) or 0
                )
            elif evidence_answer_ids:
                evidence_records += int(
                    self.db.scalar(
                        select(func.count(EvidenceCitationEntity.id)).where(
                            EvidenceCitationEntity.evidence_answer_id.in_(evidence_answer_ids)
                        )
                    )
                    or 0
                )
            elif chunk_ids:
                evidence_records += int(
                    self.db.scalar(
                        select(func.count(EvidenceCitationEntity.id)).where(
                            EvidenceCitationEntity.chunk_id.in_(chunk_ids)
                        )
                    )
                    or 0
                )
            evidence_records += int(
                self.db.scalar(
                    select(func.count(DocumentExtractedFactEntity.id)).where(
                        DocumentExtractedFactEntity.draft_id.in_(draft_ids)
                    )
                )
                or 0
            )
            evidence_records += int(
                self.db.scalar(
                    select(func.count(DocumentAgentRunEntity.id)).where(DocumentAgentRunEntity.draft_id.in_(draft_ids))
                )
                or 0
            )

        active_statuses = {"extracting", "embedding", "reasoning"}
        active_jobs = [
            job
            for job in jobs
            if job.status in active_statuses and document_job_has_live_worker(self.db, int(job.id))
        ]
        return {
            "drafts": drafts,
            "sessions": sessions,
            "documents": documents,
            "jobs": jobs,
            "evidence_records": evidence_records,
            "active_processing_jobs": len(active_jobs),
        }

    def delete_incomplete_activity(self, snapshot: dict[str, object]) -> None:
        drafts = list(snapshot["drafts"])
        sessions = list(snapshot["sessions"])
        documents = list(snapshot["documents"])
        draft_ids = [int(draft.id) for draft in drafts]
        document_ids = [int(document.id) for document in documents]

        if draft_ids:
            evidence_answer_ids = select(EvidenceAnswerEntity.id).where(EvidenceAnswerEntity.draft_id.in_(draft_ids))
            chunk_ids = select(DocumentChunkEntity.id).where(DocumentChunkEntity.draft_id.in_(draft_ids))
            page_ids = select(DocumentPageEntity.id).where(DocumentPageEntity.document_id.in_(document_ids))
            self.db.execute(
                delete(EvidenceCitationEntity).where(
                    EvidenceCitationEntity.evidence_answer_id.in_(evidence_answer_ids)
                    | EvidenceCitationEntity.chunk_id.in_(chunk_ids)
                )
            )
            self.db.execute(
                delete(DocumentExtractedFactEntity).where(DocumentExtractedFactEntity.draft_id.in_(draft_ids))
            )
            self.db.execute(delete(DocumentAgentRunEntity).where(DocumentAgentRunEntity.draft_id.in_(draft_ids)))
            self.db.execute(delete(EvidenceAnswerEntity).where(EvidenceAnswerEntity.draft_id.in_(draft_ids)))
            self.db.execute(delete(DocumentChunkEntity).where(DocumentChunkEntity.draft_id.in_(draft_ids)))
            if document_ids:
                self.db.execute(delete(DocumentPageEntity).where(DocumentPageEntity.id.in_(page_ids)))
            self.db.execute(
                delete(DocumentProcessingJobEntity).where(DocumentProcessingJobEntity.draft_id.in_(draft_ids))
            )
            if document_ids:
                self.db.execute(delete(AssessmentDocumentEntity).where(AssessmentDocumentEntity.id.in_(document_ids)))
            self.db.execute(delete(AssessmentDraftEntity).where(AssessmentDraftEntity.id.in_(draft_ids)))

        session_ids = [int(session.id) for session in sessions]
        if session_ids:
            self.db.execute(delete(AssessmentSessionEntity).where(AssessmentSessionEntity.id.in_(session_ids)))
        self.db.commit()

    def list_documents_for_draft(self, draft_id: int) -> list[AssessmentDocumentEntity]:
        return list(
            self.db.scalars(
                select(AssessmentDocumentEntity)
                .where(AssessmentDocumentEntity.draft_id == draft_id)
                .order_by(AssessmentDocumentEntity.created_at.asc())
            )
        )

    def list_documents_for_draft_ids(self, draft_ids: list[int]) -> list[AssessmentDocumentEntity]:
        if not draft_ids:
            return []
        return list(
            self.db.scalars(
                select(AssessmentDocumentEntity)
                .where(AssessmentDocumentEntity.draft_id.in_(draft_ids))
                .order_by(AssessmentDocumentEntity.created_at.asc())
            )
        )

    def get_document_by_id(self, document_id: int) -> AssessmentDocumentEntity | None:
        return self.db.scalar(
            select(AssessmentDocumentEntity).where(AssessmentDocumentEntity.id == document_id)
        )

    def get_document_counts_for_draft_ids(self, draft_ids: list[int]) -> dict[int, int]:
        if not draft_ids:
            return {}
        rows = self.db.execute(
            select(
                AssessmentDocumentEntity.draft_id,
                func.count(AssessmentDocumentEntity.id),
            )
            .where(AssessmentDocumentEntity.draft_id.in_(draft_ids))
            .group_by(AssessmentDocumentEntity.draft_id)
        ).all()
        return {int(draft_id): int(count) for draft_id, count in rows}

    def _assessments_query(
        self,
        search: str | None = None,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        company: str | None = None,
        document_backed_only: bool = False,
    ):
        query = select(AssessmentSubmissionEntity, AssessmentResultEntity).join(
            AssessmentResultEntity, AssessmentResultEntity.submission_id == AssessmentSubmissionEntity.id
        )
        if search:
            search_like = f"%{search.lower()}%"
            query = query.where(
                func.lower(AssessmentSubmissionEntity.name).like(search_like)
                | func.lower(AssessmentSubmissionEntity.company).like(search_like)
                | func.lower(AssessmentSubmissionEntity.project_name).like(search_like)
                | func.lower(AssessmentResultEntity.recommendation).like(search_like)
            )
        if company:
            company_like = f"%{company.lower()}%"
            query = query.where(func.lower(AssessmentSubmissionEntity.company).like(company_like))
        if recommendation:
            query = query.where(AssessmentResultEntity.recommendation == recommendation)
        if industry:
            query = query.where(AssessmentSubmissionEntity.industry == industry)
        if project_type:
            query = query.where(AssessmentSubmissionEntity.project_type == project_type)
        if rules_version is not None:
            query = query.where(AssessmentResultEntity.rules_version == rules_version)
        if questionnaire_version is not None:
            query = query.where(AssessmentResultEntity.questionnaire_version == questionnaire_version)
        if date_from:
            query = query.where(AssessmentSubmissionEntity.created_at >= date_from)
        if date_to:
            query = query.where(AssessmentSubmissionEntity.created_at <= date_to)
        if document_backed_only:
            query = query.where(
                select(func.count(AssessmentDocumentEntity.id))
                .where(AssessmentDocumentEntity.draft_id == AssessmentSubmissionEntity.draft_id)
                .scalar_subquery()
                > 0
            )
        return query

    def list_assessments(
        self,
        page: int,
        page_size: int,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        search: str | None = None,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        company: str | None = None,
        document_backed_only: bool = False,
    ):
        offset = (page - 1) * page_size
        sort_mapping = {
            "name": AssessmentSubmissionEntity.name,
            "company": AssessmentSubmissionEntity.company,
            "project_name": AssessmentSubmissionEntity.project_name,
            "recommendation": AssessmentResultEntity.recommendation,
            "created_at": AssessmentSubmissionEntity.created_at,
            "agile_score": AssessmentResultEntity.agile_score,
            "traditional_score": AssessmentResultEntity.traditional_score,
        }
        sort_column = sort_mapping.get(sort_by, AssessmentSubmissionEntity.created_at)
        ordered = sort_column.asc() if sort_dir == "asc" else sort_column.desc()
        rows = self.db.execute(
            self._assessments_query(
                search=search,
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                date_from=date_from,
                date_to=date_to,
                company=company,
                document_backed_only=document_backed_only,
            )
            .order_by(ordered)
            .limit(page_size)
            .offset(offset)
        ).all()
        return rows

    def count_results(
        self,
        search: str | None = None,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        company: str | None = None,
        document_backed_only: bool = False,
    ) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(
                self._assessments_query(
                    search=search,
                    recommendation=recommendation,
                    industry=industry,
                    project_type=project_type,
                    rules_version=rules_version,
                    questionnaire_version=questionnaire_version,
                    date_from=date_from,
                    date_to=date_to,
                    company=company,
                    document_backed_only=document_backed_only,
                ).subquery()
            )
        ) or 0

    def list_company_groups(
        self,
        page: int,
        page_size: int,
        sort_by: str,
        sort_dir: str,
        search: str | None = None,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        company: str | None = None,
        document_backed_only: bool = False,
    ):
        offset = (page - 1) * page_size
        base_query = self._assessments_query(
            search=search,
            recommendation=recommendation,
            industry=industry,
            project_type=project_type,
            rules_version=rules_version,
            questionnaire_version=questionnaire_version,
            date_from=date_from,
            date_to=date_to,
            company=company,
            document_backed_only=document_backed_only,
        ).subquery()
        agile_count = func.sum(case((base_query.c.recommendation == "Agile", 1), else_=0))
        traditional_count = func.sum(case((base_query.c.recommendation == "Traditional", 1), else_=0))
        group_query = (
            select(
                base_query.c.normalized_company.label("normalized_company"),
                func.count().label("submission_count"),
                func.max(base_query.c.created_at).label("latest_submission_at"),
                agile_count.label("agile_count"),
                traditional_count.label("traditional_count"),
                func.avg(base_query.c.agile_score).label("avg_agile_score"),
                func.avg(base_query.c.traditional_score).label("avg_traditional_score"),
            )
            .group_by(base_query.c.normalized_company)
        )
        sort_mapping = {
            "company": base_query.c.normalized_company,
            "submission_count": func.count(),
            "latest_submission_at": func.max(base_query.c.created_at),
            "avg_agile_score": func.avg(base_query.c.agile_score),
            "avg_traditional_score": func.avg(base_query.c.traditional_score),
        }
        sort_column = sort_mapping.get(sort_by, func.max(base_query.c.created_at))
        ordered = sort_column.asc() if sort_dir == "asc" else sort_column.desc()
        return self.db.execute(group_query.order_by(ordered).limit(page_size).offset(offset)).all()

    def count_company_groups(
        self,
        search: str | None = None,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        company: str | None = None,
        document_backed_only: bool = False,
    ) -> int:
        base_query = self._assessments_query(
            search=search,
            recommendation=recommendation,
            industry=industry,
            project_type=project_type,
            rules_version=rules_version,
            questionnaire_version=questionnaire_version,
            date_from=date_from,
            date_to=date_to,
            company=company,
            document_backed_only=document_backed_only,
        ).subquery()
        return self.db.scalar(
            select(func.count()).select_from(
                select(base_query.c.normalized_company).group_by(base_query.c.normalized_company).subquery()
            )
        ) or 0

    def list_assessments_for_companies(
        self,
        normalized_companies: list[str],
        search: str | None = None,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        company: str | None = None,
        document_backed_only: bool = False,
    ):
        if not normalized_companies:
            return []
        return self.db.execute(
            self._assessments_query(
                search=search,
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                date_from=date_from,
                date_to=date_to,
                company=company,
                document_backed_only=document_backed_only,
            )
            .where(AssessmentSubmissionEntity.normalized_company.in_(normalized_companies))
            .order_by(AssessmentSubmissionEntity.created_at.desc())
        ).all()

    def get_analytics_summary(self):
        total_submissions = self.db.scalar(select(func.count(AssessmentResultEntity.id))) or 0
        agile_recommendations = self.db.scalar(
            select(func.count(AssessmentResultEntity.id)).where(AssessmentResultEntity.recommendation == "Agile")
        ) or 0
        traditional_recommendations = self.db.scalar(
            select(func.count(AssessmentResultEntity.id)).where(
                AssessmentResultEntity.recommendation == "Traditional"
            )
        ) or 0
        avg_agile_score = self.db.scalar(select(func.avg(AssessmentResultEntity.agile_score))) or 0
        avg_traditional_score = self.db.scalar(
            select(func.avg(AssessmentResultEntity.traditional_score))
        ) or 0
        return (
            int(total_submissions),
            int(agile_recommendations),
            int(traditional_recommendations),
            round(float(avg_agile_score), 2),
            round(float(avg_traditional_score), 2),
        )

    def get_results_for_research(
        self,
        questionnaire_version: int | None = None,
        rules_version: int | None = None,
    ) -> list[AssessmentResultEntity]:
        query = select(AssessmentResultEntity)
        if questionnaire_version is not None:
            query = query.where(AssessmentResultEntity.questionnaire_version == questionnaire_version)
        if rules_version is not None:
            query = query.where(AssessmentResultEntity.rules_version == rules_version)
        return list(self.db.scalars(query))

    def get_answers_for_research(
        self,
        questionnaire_version: int | None = None,
        rules_version: int | None = None,
    ) -> list[AssessmentAnswerEntity]:
        query = select(AssessmentAnswerEntity).join(
            AssessmentResultEntity,
            AssessmentResultEntity.submission_id == AssessmentAnswerEntity.submission_id,
        )
        if questionnaire_version is not None:
            query = query.where(AssessmentResultEntity.questionnaire_version == questionnaire_version)
        if rules_version is not None:
            query = query.where(AssessmentResultEntity.rules_version == rules_version)
        return list(self.db.scalars(query))

    def get_session_summary(self, fully_answered_threshold: int) -> tuple[int, int, int, int, int]:
        opened = self.db.scalar(select(func.count(AssessmentSessionEntity.id))) or 0
        answered = self.db.scalar(
            select(func.count(AssessmentSessionEntity.id)).where(AssessmentSessionEntity.answered_count > 0)
        ) or 0
        fully_answered = self.db.scalar(
            select(func.count(AssessmentSessionEntity.id)).where(
                AssessmentSessionEntity.answered_count >= fully_answered_threshold
            )
        ) or 0
        in_progress = self.db.scalar(
            select(func.count(AssessmentSessionEntity.id)).where(
                AssessmentSessionEntity.answered_count > 0,
                AssessmentSessionEntity.completed_at.is_(None),
            )
        ) or 0
        completed = self.db.scalar(
            select(func.count(AssessmentSessionEntity.id)).where(AssessmentSessionEntity.completed_at.is_not(None))
        ) or 0
        return int(opened), int(answered), int(fully_answered), int(in_progress), int(completed)

    def get_draft_counts_for_sessions(self) -> tuple[int, int]:
        draft_created = self.db.scalar(
            select(func.count(AssessmentDraftEntity.id)).where(AssessmentDraftEntity.assessment_session_id.is_not(None))
        ) or 0
        uploaded_documents = self.db.scalar(select(func.count(AssessmentDocumentEntity.id))) or 0
        return int(draft_created), int(uploaded_documents)
