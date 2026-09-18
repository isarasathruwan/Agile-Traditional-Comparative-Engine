import csv
import io
import json
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from shutil import rmtree

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.entity.draft_entity import AssessmentDraftEntity
from app.entity.document_intelligence_entity import DocumentProcessingJobEntity, EvidenceAnswerEntity
from app.exceptions.domain_exception import ConflictException, NotFoundException, ServiceException, ValidationException
from app.model.admin_model import (
    AiAnalyticsData,
    AssessmentWorkspaceAnalyticsData,
    AnalyticsSummaryData,
    AssessmentLikertAnswerData,
    AssessmentProfileAnswerData,
    AssessmentDeleteData,
    AssessmentDetailData,
    AssessmentListItem,
    CompanyGroupItem,
    DocumentProcessingRetryData,
    IncompleteActivityData,
    DistributionsData,
    ResearchMetricsData,
    TrendPoint,
    TrendsData,
)
from app.repository.assessment_repository import AssessmentRepository
from app.repository.questionnaire_repository import QuestionnaireRepository
from app.repository.rule_repository import RuleRepository
from app.service.ai_demo_service import AIDemoService
from app.util.encryption import DocumentCipher
from app.service.assessment_service import AssessmentService
from app.service.traditional_advisor_service import TraditionalAdvisorService
from app.service.questionnaire_service import DEFAULT_QUESTIONNAIRE
from app.util.response import GenericResponse, PaginatedResponse

logger = logging.getLogger(__name__)


class AdminService:
    DEPENDENT_VARIABLE_KEYS = {
        "timeline_adherence": "Timeline Constraint Pressure",
        "budget_accuracy": "Budget Constraint Pressure",
        "product_quality": "Quality Assurance Pressure",
        "user_satisfaction": "User Feedback Need",
        "communication_effectiveness": "Collaboration Readiness",
        "security_integration": "Security and Assurance Criticality",
        "system_integration_effectiveness": "Integration and Dependency Complexity",
    }

    def __init__(self):
        self.ai_demo_service = AIDemoService()
        self.traditional_advisor_service = TraditionalAdvisorService()

    @staticmethod
    def _variance(values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        mean_value = sum(values) / len(values)
        return sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)

    @staticmethod
    def _serialize_assessment_list_item(submission, result, has_documents: bool) -> AssessmentListItem:
        return AssessmentListItem(
            submission_id=submission.id,
            name=submission.name,
            company=submission.company,
            project_name=submission.project_name,
            recommendation=result.recommendation,
            agile_score=result.agile_score,
            traditional_score=result.traditional_score,
            has_documents=has_documents,
            questionnaire_version=result.questionnaire_version,
            created_at=submission.created_at.isoformat(),
        )

    @staticmethod
    def _serialize_document(document: object) -> dict[str, object]:
        document_id = int(getattr(document, "id"))
        return {
            "id": document_id,
            "filename": str(getattr(document, "filename")),
            "content_type": str(getattr(document, "content_type")),
            "file_size": int(getattr(document, "file_size")),
            "status": str(getattr(document, "status")),
            "created_at": getattr(document, "created_at").isoformat(),
            "preview_url": f"/api/v1/admin/assessment-documents/{document_id}/preview",
            "download_url": f"/api/v1/admin/assessment-documents/{document_id}/download",
        }

    @staticmethod
    def _cleanup_document_storage(paths: list[Path]) -> int:
        seen_directories: set[Path] = set()
        failures = 0
        for path in paths:
            if path.name == "mock_path":
                continue
            try:
                if path.exists():
                    path.unlink()
                seen_directories.add(path.parent)
            except FileNotFoundError:
                continue
            except OSError:
                failures += 1
                logger.warning("Unable to remove document file at %s", path, exc_info=True)
        for directory in seen_directories:
            try:
                if directory.exists() and not any(directory.iterdir()):
                    rmtree(directory)
            except OSError:
                failures += 1
                logger.warning("Unable to remove empty document directory at %s", directory, exc_info=True)
        return failures

    @staticmethod
    def _pearson(x: list[float], y: list[float]) -> float | None:
        if len(x) < 2 or len(y) < 2 or len(x) != len(y):
            return None
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        num = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
        den_x = math.sqrt(sum((a - mean_x) ** 2 for a in x))
        den_y = math.sqrt(sum((b - mean_y) ** 2 for b in y))
        if den_x == 0 or den_y == 0:
            return None
        return round(num / (den_x * den_y), 4)

    @staticmethod
    def _welch_t_test(group_a: list[float], group_b: list[float]) -> dict[str, float | int | None]:
        if len(group_a) < 2 or len(group_b) < 2:
            return {
                "n_group_a": len(group_a),
                "n_group_b": len(group_b),
                "mean_group_a": round(sum(group_a) / len(group_a), 4) if group_a else None,
                "mean_group_b": round(sum(group_b) / len(group_b), 4) if group_b else None,
                "t_statistic": None,
                "df": None,
            }
        mean_a = sum(group_a) / len(group_a)
        mean_b = sum(group_b) / len(group_b)
        var_a = AdminService._variance(group_a)
        var_b = AdminService._variance(group_b)
        if var_a is None or var_b is None:
            return {
                "n_group_a": len(group_a),
                "n_group_b": len(group_b),
                "mean_group_a": round(mean_a, 4),
                "mean_group_b": round(mean_b, 4),
                "t_statistic": None,
                "df": None,
            }

        se_sq = (var_a / len(group_a)) + (var_b / len(group_b))
        if se_sq == 0:
            return {
                "n_group_a": len(group_a),
                "n_group_b": len(group_b),
                "mean_group_a": round(mean_a, 4),
                "mean_group_b": round(mean_b, 4),
                "t_statistic": None,
                "df": None,
            }

        t_stat = (mean_a - mean_b) / math.sqrt(se_sq)
        numerator = se_sq**2
        denominator = ((var_a / len(group_a)) ** 2) / (len(group_a) - 1) + (
            (var_b / len(group_b)) ** 2
        ) / (len(group_b) - 1)
        df = numerator / denominator if denominator else None
        return {
            "n_group_a": len(group_a),
            "n_group_b": len(group_b),
            "mean_group_a": round(mean_a, 4),
            "mean_group_b": round(mean_b, 4),
            "t_statistic": round(t_stat, 4),
            "df": round(df, 4) if df is not None else None,
        }

    @staticmethod
    def _dependent_variables_from_result(result) -> dict[str, float]:
        if result.dependent_variable_scores:
            return {key: float(value) for key, value in result.dependent_variable_scores.items()}
        flexibility = float(result.flexibility_score)
        performance = float(result.performance_score)
        strictness = float(result.strictness_score)
        product_quality = (performance + strictness) / 2
        return {
            "timeline_adherence": performance,
            "budget_accuracy": performance,
            "product_quality": product_quality,
            "user_satisfaction": flexibility,
            "communication_effectiveness": flexibility,
            "security_integration": strictness,
            "system_integration_effectiveness": strictness,
        }

    @classmethod
    def _dependent_variable_means(cls, rows: list) -> dict[str, float]:
        if not rows:
            return {key: 0.0 for key in cls.DEPENDENT_VARIABLE_KEYS}
        aggregate = {key: 0.0 for key in cls.DEPENDENT_VARIABLE_KEYS}
        for row in rows:
            values = cls._dependent_variables_from_result(row)
            for key in aggregate:
                aggregate[key] += values[key]
        return {key: round(total / len(rows), 4) for key, total in aggregate.items()}

    @staticmethod
    def _submission_profile_value(submission, profile_key: str) -> str:
        mapping = {
            "name": "name",
            "role": "role",
            "company": "company",
            "industry": "industry",
            "orgSize": "org_size",
            "projectName": "project_name",
            "projectType": "project_type",
            "duration": "duration",
            "teamSize": "team_size",
            "budget": "budget",
        }
        attr = mapping.get(profile_key, profile_key)
        return str(getattr(submission, attr, "") or "")

    @staticmethod
    def _submission_profile_other_text(submission, profile_key: str) -> str | None:
        other_inputs = getattr(submission, "profile_other_inputs", None) or {}
        value = other_inputs.get(profile_key)
        if not value:
            return None
        return str(value)

    @staticmethod
    def _confidence_distribution(rows: list) -> dict[str, int]:
        distribution = {"high": 0, "moderate": 0, "close": 0}
        for row in rows:
            report = row.decision_report or {}
            confidence = str(report.get("confidence_level") or "")
            if confidence in distribution:
                distribution[confidence] += 1
                continue
            score_gap = abs(float(row.agile_score) - float(row.traditional_score))
            fallback = "high" if score_gap >= 20 else "moderate" if score_gap >= 10 else "close"
            distribution[fallback] += 1
        return distribution

    @staticmethod
    def _risk_flag_counts(rows: list) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            report = row.decision_report or {}
            for flag in report.get("risk_flags", []):
                if not isinstance(flag, dict):
                    continue
                key = str(flag.get("key") or flag.get("label") or "unknown")
                counts[key] = counts.get(key, 0) + 1
        return counts

    @staticmethod
    def _strategy_distributions(rows: list) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        readiness = {"high": 0, "moderate": 0, "low": 0}
        delivery: dict[str, int] = {}
        options: dict[str, int] = {}
        for row in rows:
            report = row.decision_report or {}
            strategy = report.get("strategy_profile")
            if not isinstance(strategy, dict):
                continue
            hybrid = strategy.get("hybrid_readiness")
            if isinstance(hybrid, dict):
                level = str(hybrid.get("level") or "")
                if level in readiness:
                    readiness[level] += 1
            delivery_key = str(strategy.get("delivery_strategy") or "")
            if delivery_key:
                delivery[delivery_key] = delivery.get(delivery_key, 0) + 1
            for option in strategy.get("strategy_options", []):
                if not isinstance(option, dict):
                    continue
                key = str(option.get("key") or option.get("label") or "")
                if key:
                    options[key] = options.get(key, 0) + 1
        return readiness, delivery, options

    def _cronbach_alpha(self, rows: list[dict[str, int]]) -> float | None:
        if len(rows) < 2:
            return None
        item_keys = sorted({key for row in rows for key in row.keys()})
        if len(item_keys) < 2:
            return None
        complete_rows = [row for row in rows if all(key in row for key in item_keys)]
        if len(complete_rows) < 2:
            return None
        item_variances: list[float] = []
        total_scores: list[float] = []
        for key in item_keys:
            values = [float(row[key]) for row in complete_rows]
            variance = self._variance(values)
            if variance is None:
                return None
            item_variances.append(variance)
        for row in complete_rows:
            total_scores.append(float(sum(row[key] for key in item_keys)))
        total_variance = self._variance(total_scores)
        if total_variance is None or total_variance == 0:
            return None
        n_items = len(item_keys)
        alpha = (n_items / (n_items - 1)) * (1 - (sum(item_variances) / total_variance))
        return round(alpha, 4)

    def get_analytics_summary(self, db: Session) -> GenericResponse[AnalyticsSummaryData]:
        logger.info("AdminService.get_analytics_summary started.")
        try:
            repo = AssessmentRepository(db)
            total, agile, traditional, avg_agile, avg_traditional = repo.get_analytics_summary()
            data = AnalyticsSummaryData(
                total_submissions=total,
                agile_recommendations=agile,
                traditional_recommendations=traditional,
                avg_agile_score=avg_agile,
                avg_traditional_score=avg_traditional,
            )
            logger.info("AdminService.get_analytics_summary completed.")
            return GenericResponse.success_response(message="Analytics summary fetched.", data=data)
        except Exception:
            logger.exception("AdminService.get_analytics_summary failed unexpectedly.")
            raise ServiceException("Unable to fetch analytics summary.") from None

    def list_assessments(
        self,
        db: Session,
        page: int,
        page_size: int,
        sort_by: str,
        sort_dir: str,
        search: str | None = None,
        company: str | None = None,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        document_backed_only: bool = False,
    ) -> PaginatedResponse[list[AssessmentListItem]]:
        logger.info("AdminService.list_assessments started page=%s page_size=%s", page, page_size)
        try:
            repo = AssessmentRepository(db)
            rows = repo.list_assessments(
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_dir=sort_dir,
                search=search,
                company=company,
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                date_from=date_from,
                date_to=date_to,
                document_backed_only=document_backed_only,
            )
            total = repo.count_results(
                search=search,
                company=company,
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                date_from=date_from,
                date_to=date_to,
                document_backed_only=document_backed_only,
            )
            draft_ids = [submission.draft_id for submission, _ in rows if submission.draft_id is not None]
            document_counts = repo.get_document_counts_for_draft_ids([int(draft_id) for draft_id in draft_ids])
            data = [
                self._serialize_assessment_list_item(
                    submission,
                    result,
                    bool(submission.draft_id and document_counts.get(int(submission.draft_id), 0) > 0),
                )
                for submission, result in rows
            ]
            logger.info("AdminService.list_assessments completed records=%s", len(data))
            return PaginatedResponse.success_paginated_response(
                message="Assessments fetched.",
                data=data,
                page=page,
                page_size=page_size,
                total_records=total,
            )
        except Exception:
            logger.exception("AdminService.list_assessments failed unexpectedly.")
            raise ServiceException("Unable to fetch assessments.") from None

    def list_grouped_assessments_by_company(
        self,
        db: Session,
        page: int,
        page_size: int,
        sort_by: str,
        sort_dir: str,
        search: str | None = None,
        company: str | None = None,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        document_backed_only: bool = False,
    ) -> PaginatedResponse[list[CompanyGroupItem]]:
        logger.info("AdminService.list_grouped_assessments_by_company started")
        try:
            repo = AssessmentRepository(db)
            summary_rows = repo.list_company_groups(
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_dir=sort_dir,
                search=search,
                company=company,
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                date_from=date_from,
                date_to=date_to,
                document_backed_only=document_backed_only,
            )
            normalized_companies = [str(row.normalized_company or "") for row in summary_rows]
            item_rows = repo.list_assessments_for_companies(
                normalized_companies,
                search=search,
                company=company,
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                date_from=date_from,
                date_to=date_to,
                document_backed_only=document_backed_only,
            )
            item_map: dict[str, list[AssessmentListItem]] = {key: [] for key in normalized_companies}
            company_map: dict[str, str] = {key: key for key in normalized_companies}
            draft_ids = [submission.draft_id for submission, _ in item_rows if submission.draft_id is not None]
            document_counts = repo.get_document_counts_for_draft_ids([int(draft_id) for draft_id in draft_ids])
            for submission, result in item_rows:
                normalized_company = str(submission.normalized_company or submission.company)
                company_map[normalized_company] = submission.company
                item_map.setdefault(normalized_company, []).append(
                    self._serialize_assessment_list_item(
                        submission,
                        result,
                        bool(submission.draft_id and document_counts.get(int(submission.draft_id), 0) > 0),
                    )
                )

            total_records = repo.count_company_groups(
                search=search,
                company=company,
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                date_from=date_from,
                date_to=date_to,
                document_backed_only=document_backed_only,
            )
            group_items = [
                CompanyGroupItem(
                    company=company_map[str(row.normalized_company or "")],
                    normalized_company=str(row.normalized_company or ""),
                    submission_count=int(row.submission_count),
                    latest_submission_at=row.latest_submission_at.isoformat(),
                    agile_count=int(row.agile_count or 0),
                    traditional_count=int(row.traditional_count or 0),
                    avg_agile_score=round(float(row.avg_agile_score or 0.0), 2),
                    avg_traditional_score=round(float(row.avg_traditional_score or 0.0), 2),
                    items=item_map.get(str(row.normalized_company or ""), []),
                )
                for row in summary_rows
            ]

            return PaginatedResponse.success_paginated_response(
                message="Grouped assessments fetched.",
                data=group_items,
                page=page,
                page_size=page_size,
                total_records=total_records,
            )
        except Exception:
            logger.exception("AdminService.list_grouped_assessments_by_company failed unexpectedly.")
            raise ServiceException("Unable to fetch grouped assessments.") from None

    def get_assessment_detail(self, db: Session, submission_id: int) -> GenericResponse[AssessmentDetailData]:
        logger.info("AdminService.get_assessment_detail started submission_id=%s", submission_id)
        try:
            repo = AssessmentRepository(db)
            submission = repo.get_submission_by_id(submission_id)
            result = repo.get_result_by_submission_id(submission_id)
            if not submission or not result:
                raise NotFoundException("Assessment not found.")

            questionnaire = QuestionnaireRepository(db).get_by_version(result.questionnaire_version)
            questionnaire_payload = (
                json.loads(questionnaire.payload_json) if questionnaire else DEFAULT_QUESTIONNAIRE.model_dump()
            )
            profile_questions = questionnaire_payload.get("profile_questions", [])
            likert_questions = questionnaire_payload.get("likert_questions", [])
            likert_prompt_map = {str(item.get("question_id")): item for item in likert_questions}
            answers = repo.get_answers_by_submission_id(submission_id)
            documents = repo.list_documents_for_draft(submission.draft_id) if submission.draft_id else []
            construct_scores = {
                "FLEXIBILITY": result.flexibility_score,
                "PERFORMANCE": result.performance_score,
                "STRICTNESS": result.strictness_score,
            }
            dependent_scores = result.dependent_variable_scores or AdminService._dependent_variables_from_result(result)
            score_gap = round(abs(float(result.agile_score) - float(result.traditional_score)), 2)
            confidence = "high" if score_gap >= 20 else "moderate" if score_gap >= 10 else "close"
            strongest = max(dependent_scores.items(), key=lambda item: item[1])
            weakest = min(dependent_scores.items(), key=lambda item: item[1])
            insights = {
                "recommended_direction": result.recommendation,
                "strongest_dimension": strongest[0],
                "strongest_score": strongest[1],
                "weakest_dimension": weakest[0],
                "weakest_score": weakest[1],
                "score_gap": score_gap,
                "confidence_level": confidence,
            }
            decision_report = result.decision_report or {}
            if "strategy_profile" not in decision_report:
                decision_report = {
                    **decision_report,
                    "strategy_profile": AssessmentService._strategy_profile(
                        recommendation=result.recommendation,
                        agile_score=result.agile_score,
                        traditional_score=result.traditional_score,
                        construct_scores=construct_scores,
                        profile=submission,
                    ),
                }

            data = AssessmentDetailData(
                submission_id=submission_id,
                profile_answers=[
                    AssessmentProfileAnswerData(
                        question_id=str(item.get("question_id", "")),
                        prompt=str(item.get("prompt", item.get("profile_key", ""))),
                        profile_key=str(item.get("profile_key", "")),
                        answer=(
                            self._submission_profile_other_text(submission, str(item.get("profile_key", "")))
                            or self._submission_profile_value(submission, str(item.get("profile_key", "")))
                        ),
                        selected_option=(
                            self._submission_profile_value(submission, str(item.get("profile_key", "")))
                            if str(item.get("kind", "")) == "pill"
                            else None
                        ),
                        other_text=self._submission_profile_other_text(submission, str(item.get("profile_key", ""))),
                    )
                    for item in profile_questions
                ],
                likert_answers=[
                    AssessmentLikertAnswerData(
                        question_id=answer.question_key,
                        prompt=str(likert_prompt_map.get(answer.question_key, {}).get("prompt", answer.question_key)),
                        construct=str(
                            likert_prompt_map.get(answer.question_key, {}).get("construct", answer.construct)
                        ),
                        answer=answer.value,
                    )
                    for answer in answers
                ],
                recommendation=result.recommendation,
                agile_score=result.agile_score,
                traditional_score=result.traditional_score,
                construct_scores=construct_scores,
                dependent_variable_scores=dependent_scores,
                insights=insights,
                decision_report=decision_report,
                ai_demo_trace=result.ai_demo_trace or [],
                ai_demo_summary=result.ai_demo_summary
                or {
                    "documents_processed": 0,
                    "trace_steps": 0,
                    "candidate_signals": [],
                    "document_filenames": [],
                    "demo_mode": True,
                    "explanation_scope": "candidate_signals_only",
                },
                documents=[self._serialize_document(document) for document in documents],
                traditional_advisor=self.traditional_advisor_service.get_for_admin(db, submission_id),
                rules_version=result.rules_version,
                questionnaire_version=result.questionnaire_version,
                created_at=result.created_at.isoformat(),
            )
            logger.info("AdminService.get_assessment_detail completed submission_id=%s", submission_id)
            return GenericResponse.success_response("Assessment detail fetched.", data=data)
        except NotFoundException:
            raise
        except Exception:
            logger.exception("AdminService.get_assessment_detail failed unexpectedly.")
            raise ServiceException("Unable to fetch assessment detail.") from None

    def delete_assessment(self, db: Session, submission_id: int) -> GenericResponse[AssessmentDeleteData]:
        logger.info("AdminService.delete_assessment started submission_id=%s", submission_id)
        try:
            repo = AssessmentRepository(db)
            submission = repo.get_submission_by_id(submission_id)
            if not submission:
                raise NotFoundException("Assessment not found.")

            stored_paths = [
                Path(document.storage_path)
                for document in (repo.list_documents_for_draft(submission.draft_id) if submission.draft_id else [])
            ]
            deleted = repo.delete_assessment_bundle(submission_id)
            self._cleanup_document_storage(stored_paths)
            data = AssessmentDeleteData(
                submission_id=submission_id,
                deleted_documents=len(deleted["deleted_documents"]),
                deleted_session=bool(deleted["deleted_session"]),
                deleted_draft=bool(deleted["deleted_draft"]),
            )
            logger.info("AdminService.delete_assessment completed submission_id=%s", submission_id)
            return GenericResponse.success_response("Assessment deleted.", data=data)
        except NotFoundException:
            raise
        except Exception:
            db.rollback()
            logger.exception("AdminService.delete_assessment failed unexpectedly.")
            raise ServiceException("Unable to delete assessment.") from None

    @staticmethod
    def _serialize_incomplete_activity(
        snapshot: dict[str, object],
        file_cleanup_failures: int = 0,
    ) -> IncompleteActivityData:
        documents = list(snapshot["documents"])
        return IncompleteActivityData(
            incomplete_sessions=len(list(snapshot["sessions"])),
            unsubmitted_drafts=len(list(snapshot["drafts"])),
            uploaded_documents=len(documents),
            processing_jobs=len(list(snapshot["jobs"])),
            evidence_records=int(snapshot["evidence_records"]),
            stored_file_count=len(
                [document for document in documents if Path(document.storage_path).name != "mock_path"]
            ),
            stored_file_bytes=sum(int(document.file_size) for document in documents),
            active_processing_jobs=int(snapshot["active_processing_jobs"]),
            file_cleanup_failures=file_cleanup_failures,
        )

    def get_incomplete_activity(self, db: Session) -> GenericResponse[IncompleteActivityData]:
        logger.info("AdminService.get_incomplete_activity started.")
        try:
            snapshot = AssessmentRepository(db).get_incomplete_activity_snapshot()
            return GenericResponse.success_response(
                "Incomplete assessment activity fetched.",
                data=self._serialize_incomplete_activity(snapshot),
            )
        except Exception:
            logger.exception("AdminService.get_incomplete_activity failed unexpectedly.")
            raise ServiceException("Unable to inspect incomplete assessment activity.") from None

    def reset_incomplete_activity(
        self,
        db: Session,
        confirmation: str,
    ) -> GenericResponse[IncompleteActivityData]:
        logger.info("AdminService.reset_incomplete_activity started.")
        if confirmation != "RESET INCOMPLETE DATA":
            raise ValidationException("Type RESET INCOMPLETE DATA to confirm this action.")
        try:
            repo = AssessmentRepository(db)
            snapshot = repo.get_incomplete_activity_snapshot(lock=True)
            if int(snapshot["active_processing_jobs"]) > 0:
                db.rollback()
                raise ConflictException(
                    "Incomplete activity is still being processed. Wait for processing to finish, then try again."
                )
            stored_paths = [Path(document.storage_path) for document in list(snapshot["documents"])]
            data = self._serialize_incomplete_activity(snapshot)
            repo.delete_incomplete_activity(snapshot)
            failures = self._cleanup_document_storage(stored_paths)
            data.file_cleanup_failures = failures
            logger.info(
                "AdminService.reset_incomplete_activity completed sessions=%s drafts=%s documents=%s file_failures=%s",
                data.incomplete_sessions,
                data.unsubmitted_drafts,
                data.uploaded_documents,
                failures,
            )
            message = (
                "Incomplete assessment activity deleted."
                if failures == 0
                else "Incomplete records were deleted, but some stored files could not be removed."
            )
            return GenericResponse.success_response(message, data=data)
        except (ConflictException, ValidationException):
            raise
        except Exception:
            db.rollback()
            logger.exception("AdminService.reset_incomplete_activity failed unexpectedly.")
            raise ServiceException("Unable to reset incomplete assessment activity.") from None

    def retry_document_processing(
        self, db: Session, submission_id: int
    ) -> GenericResponse[DocumentProcessingRetryData]:
        """Queue failed documents without changing the draft's captured questionnaire or rules."""
        logger.info("AdminService.retry_document_processing started submission_id=%s", submission_id)
        try:
            repo = AssessmentRepository(db)
            submission = repo.get_submission_by_id(submission_id)
            if not submission or not submission.draft_id:
                raise NotFoundException("Assessment draft not found.")

            draft = repo.get_draft_by_id(submission.draft_id)
            if not draft:
                raise NotFoundException("Assessment draft not found.")

            retryable_documents = [
                document
                for document in repo.list_documents_for_draft(draft.id)
                if document.status in {"failed", "unsupported"}
            ]
            for document in retryable_documents:
                document.status = "uploaded"
                db.add(document)
            if retryable_documents:
                draft.status = "processing"
                db.add_all(
                    [
                        draft,
                        DocumentProcessingJobEntity(
                            draft_id=draft.id,
                            document_id=None,
                            status="queued",
                        ),
                    ]
                )
                db.commit()

            data = DocumentProcessingRetryData(
                submission_id=submission_id,
                queued_documents=len(retryable_documents),
            )
            message = (
                f"Queued one complete document batch with {len(retryable_documents)} retryable file(s)."
                if retryable_documents
                else "There are no failed documents to retry."
            )
            return GenericResponse.success_response(message, data=data)
        except NotFoundException:
            raise
        except Exception:
            db.rollback()
            logger.exception("AdminService.retry_document_processing failed unexpectedly.")
            raise ServiceException("Unable to retry document processing.") from None

    def get_trends(
        self,
        db: Session,
        days: int,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
    ) -> GenericResponse[TrendsData]:
        try:
            repo = AssessmentRepository(db)
            now = datetime.utcnow()
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            rows = repo.list_assessments(
                page=1,
                page_size=200000,
                sort_by="created_at",
                sort_dir="asc",
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                date_from=date_from - timedelta(days=max(days - 1, 0)),
                date_to=now,
            )
            buckets: dict[str, list] = {}
            for submission, result in rows:
                bucket = submission.created_at.date().isoformat()
                buckets.setdefault(bucket, []).append(result)
            points: list[TrendPoint] = []
            for bucket in sorted(buckets.keys()):
                items = buckets[bucket]
                total = len(items)
                agile = len([item for item in items if item.recommendation == "Agile"])
                traditional = total - agile
                avg_agile = sum(float(item.agile_score) for item in items) / total if total else 0.0
                avg_traditional = sum(float(item.traditional_score) for item in items) / total if total else 0.0
                points.append(
                    TrendPoint(
                        bucket=bucket,
                        total_submissions=total,
                        agile_recommendations=agile,
                        traditional_recommendations=traditional,
                        avg_agile_score=round(avg_agile, 2),
                        avg_traditional_score=round(avg_traditional, 2),
                    )
                )
            return GenericResponse.success_response("Trends fetched.", data=TrendsData(points=points))
        except Exception:
            logger.exception("AdminService.get_trends failed unexpectedly.")
            raise ServiceException("Unable to fetch trends.") from None

    def get_distributions(
        self,
        db: Session,
        recommendation: str | None = None,
        industry: str | None = None,
        project_type: str | None = None,
        rules_version: int | None = None,
        questionnaire_version: int | None = None,
    ) -> GenericResponse[DistributionsData]:
        try:
            repo = AssessmentRepository(db)
            rows = repo.list_assessments(
                page=1,
                page_size=200000,
                sort_by="created_at",
                sort_dir="desc",
                recommendation=recommendation,
                industry=industry,
                project_type=project_type,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
            )
            results = [result for _, result in rows]
            rec_dist = {
                "Agile": len([item for item in results if item.recommendation == "Agile"]),
                "Traditional": len([item for item in results if item.recommendation == "Traditional"]),
            }
            confidence = self._confidence_distribution(results)
            risks = self._risk_flag_counts(results)
            data = DistributionsData(
                recommendation_distribution=rec_dist,
                confidence_distribution=confidence,
                risk_flag_distribution=risks,
            )
            return GenericResponse.success_response("Distributions fetched.", data=data)
        except Exception:
            logger.exception("AdminService.get_distributions failed unexpectedly.")
            raise ServiceException("Unable to fetch distributions.") from None

    def get_assessment_workspace_analytics(self, db: Session) -> GenericResponse[AssessmentWorkspaceAnalyticsData]:
        try:
            repo = AssessmentRepository(db)
            rows = repo.list_assessments(page=1, page_size=200000, sort_by="created_at", sort_dir="desc")
            results = [result for _, result in rows]
            active_questionnaire = QuestionnaireRepository(db).get_active()
            questionnaire_payload = (
                json.loads(active_questionnaire.payload_json)
                if active_questionnaire
                else DEFAULT_QUESTIONNAIRE.model_dump()
            )
            fully_answered_threshold = len(questionnaire_payload.get("profile_questions", [])) + len(
                questionnaire_payload.get("likert_questions", [])
            )
            opened, answered, fully_answered, in_progress, completed = repo.get_session_summary(
                fully_answered_threshold=max(fully_answered_threshold, 1)
            )
            draft_created, uploaded_documents = repo.get_draft_counts_for_sessions()
            draft_ids = [submission.draft_id for submission, _ in rows if submission.draft_id is not None]
            document_counts = repo.get_document_counts_for_draft_ids([int(draft_id) for draft_id in draft_ids])
            documented_rows = [
                result
                for submission, result in rows
                if submission.draft_id and document_counts.get(int(submission.draft_id), 0) > 0
            ]
            ready_jobs = db.scalar(
                select(func.count(DocumentProcessingJobEntity.id)).where(DocumentProcessingJobEntity.status == "ready")
            ) or 0
            failed_jobs = db.scalar(
                select(func.count(DocumentProcessingJobEntity.id)).where(DocumentProcessingJobEntity.status.in_(["failed", "unsupported"]))
            ) or 0
            evidence_suggested = db.scalar(
                select(func.count(EvidenceAnswerEntity.id)).where(EvidenceAnswerEntity.evidence_status == "suggested")
            ) or 0
            evidence_confirmed = db.scalar(
                select(func.count(EvidenceAnswerEntity.id)).where(EvidenceAnswerEntity.final_value.is_not(None))
            ) or 0
            neutral_fallbacks = db.scalar(
                select(func.count(EvidenceAnswerEntity.id)).where(EvidenceAnswerEntity.evidence_status == "no_evidence")
            ) or 0
            data = AssessmentWorkspaceAnalyticsData(
                opened_assessments=opened,
                answered_assessments=answered,
                fully_answered_assessments=fully_answered,
                in_progress_assessments=in_progress,
                completed_submissions=completed,
                completion_rate=round((completed / opened) * 100, 2) if opened else 0.0,
                draft_created_count=draft_created,
                uploaded_document_count=uploaded_documents,
                document_backed_assessments=len(documented_rows),
                total_documents_processed=sum(
                    int((result.ai_demo_summary or {}).get("documents_processed", 0))
                    for result in documented_rows
                ),
                average_trace_steps=round(
                    sum(len(result.ai_demo_trace or []) for result in results) / len(results), 2
                )
                if results
                else 0.0,
                stage_frequency=self.ai_demo_service.aggregate_stage_frequency(results),
                candidate_signal_frequency=self.ai_demo_service.aggregate_candidate_signal_frequency(results),
                processing_ready_count=int(ready_jobs),
                processing_failed_count=int(failed_jobs),
                evidence_suggested_count=int(evidence_suggested),
                evidence_confirmed_count=int(evidence_confirmed),
                neutral_fallback_count=int(neutral_fallbacks),
            )
            return GenericResponse.success_response("Assessment workspace analytics fetched.", data=data)
        except Exception:
            logger.exception("AdminService.get_assessment_workspace_analytics failed unexpectedly.")
            raise ServiceException("Unable to fetch assessment workspace analytics.") from None

    def get_ai_analytics(self, db: Session) -> GenericResponse[AiAnalyticsData]:
        try:
            repo = AssessmentRepository(db)
            rows = repo.list_assessments(page=1, page_size=200000, sort_by="created_at", sort_dir="desc")
            results = [result for _, result in rows]
            documented_rows = [
                (submission, result)
                for submission, result in rows
                if int((result.ai_demo_summary or {}).get("documents_processed", 0)) > 0
            ]
            duplicate_rejections = db.scalar(select(func.sum(AssessmentDraftEntity.duplicate_rejection_count))) or 0
            latest_activity = [
                {
                    "submission_id": submission.id,
                    "company": submission.company,
                    "project_name": submission.project_name,
                    "recommendation": result.recommendation,
                    "documents_processed": int((result.ai_demo_summary or {}).get("documents_processed", 0)),
                    "trace_steps": len(result.ai_demo_trace or []),
                    "created_at": submission.created_at.isoformat(),
                }
                for submission, result in documented_rows[:8]
            ]
            data = AiAnalyticsData(
                total_documented_assessments=len(documented_rows),
                total_documents_processed=sum(
                    int((result.ai_demo_summary or {}).get("documents_processed", 0))
                    for _, result in documented_rows
                ),
                duplicate_rejections=int(duplicate_rejections),
                average_trace_steps=round(
                    sum(len(result.ai_demo_trace or []) for result in results) / len(results), 2
                )
                if results
                else 0.0,
                stage_frequency=self.ai_demo_service.aggregate_stage_frequency(results),
                candidate_signal_frequency=self.ai_demo_service.aggregate_candidate_signal_frequency(results),
                latest_activity=latest_activity,
            )
            return GenericResponse.success_response("AI analytics fetched.", data=data)
        except Exception:
            logger.exception("AdminService.get_ai_analytics failed unexpectedly.")
            raise ServiceException("Unable to fetch AI analytics.") from None

    def export_assessments_csv(self, db: Session) -> io.StringIO:
        logger.info("AdminService.export_assessments_csv started.")
        try:
            rows = AssessmentRepository(db).list_assessments(page=1, page_size=100000)
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "submission_id",
                    "name",
                    "company",
                    "project_name",
                    "recommendation",
                    "agile_score",
                    "traditional_score",
                    "questionnaire_version",
                    "created_at",
                ]
            )
            for submission, result in rows:
                writer.writerow(
                    [
                        submission.id,
                        submission.name,
                        submission.company,
                        submission.project_name,
                        result.recommendation,
                        result.agile_score,
                        result.traditional_score,
                        result.questionnaire_version,
                        submission.created_at.isoformat(),
                    ]
                )
            output.seek(0)
            logger.info("AdminService.export_assessments_csv completed.")
            return output
        except Exception:
            logger.exception("AdminService.export_assessments_csv failed unexpectedly.")
            raise ServiceException("Unable to export assessment data.") from None

    def get_document_file(self, db: Session, document_id: int) -> Path:
        try:
            document = AssessmentRepository(db).get_document_by_id(document_id)
            if not document:
                raise NotFoundException("Document not found.")
            path = Path(document.storage_path)
            if not path.exists():
                raise NotFoundException("Document file not found.")
            return path
        except NotFoundException:
            raise
        except Exception:
            logger.exception("AdminService.get_document_file failed unexpectedly.")
            raise ServiceException("Unable to fetch document file.") from None

    def get_document_content(self, db: Session, document_id: int) -> tuple[bytes, str, str]:
        """Decrypt an authorized document only for the lifetime of the response."""
        try:
            repo = AssessmentRepository(db)
            document = repo.get_document_by_id(document_id)
            if not document:
                raise NotFoundException("Document not found.")
            path = Path(document.storage_path)
            if not path.exists():
                raise NotFoundException("Document file not found.")
            if not document.encryption_nonce:
                return path.read_bytes(), document.filename, document.content_type
            draft = repo.get_draft_by_id(document.draft_id)
            if not draft:
                raise NotFoundException("Document draft not found.")
            ciphertext = path.read_text(encoding="utf-8")
            content = DocumentCipher().decrypt(ciphertext, document.encryption_nonce, draft.session_id.encode("utf-8"))
            return content, document.filename, document.content_type
        except NotFoundException:
            raise
        except Exception:
            logger.exception("AdminService.get_document_content failed unexpectedly.")
            raise ServiceException("Unable to decrypt document.") from None

    def get_research_metrics(
        self,
        db: Session,
        questionnaire_version: int | None = None,
        rules_version: int | None = None,
    ) -> GenericResponse[ResearchMetricsData]:
        logger.info("AdminService.get_research_metrics started.")
        try:
            repo = AssessmentRepository(db)
            active_questionnaire = QuestionnaireRepository(db).get_active()
            active_rule = RuleRepository(db).get_active()
            selected_questionnaire_version = questionnaire_version or (
                active_questionnaire.version if active_questionnaire else 1
            )
            selected_rules_version = rules_version or (active_rule.version if active_rule else 1)
            results = repo.get_results_for_research(
                questionnaire_version=selected_questionnaire_version,
                rules_version=selected_rules_version,
            )
            answers = repo.get_answers_for_research(
                questionnaire_version=selected_questionnaire_version,
                rules_version=selected_rules_version,
            )

            answer_map: dict[int, dict[str, int]] = {}
            construct_rows: dict[str, list[dict[str, int]]] = {
                "FLEXIBILITY": [],
                "PERFORMANCE": [],
                "STRICTNESS": [],
            }
            for answer in answers:
                answer_map.setdefault(answer.submission_id, {})[answer.question_key] = answer.value
            answers_by_submission: dict[int, list] = {}
            for answer in answers:
                answers_by_submission.setdefault(answer.submission_id, []).append(answer)
            for submission_id in answer_map:
                grouped: dict[str, dict[str, int]] = {
                    "FLEXIBILITY": {},
                    "PERFORMANCE": {},
                    "STRICTNESS": {},
                }
                for answer in answers_by_submission.get(submission_id, []):
                    grouped[answer.construct][answer.question_key] = answer.value
                for construct in grouped:
                    if grouped[construct]:
                        construct_rows[construct].append(grouped[construct])

            flexibility = [result.flexibility_score for result in results]
            performance = [result.performance_score for result in results]
            strictness = [result.strictness_score for result in results]
            agile = [result.agile_score for result in results]
            traditional = [result.traditional_score for result in results]
            agile_group = [result for result in results if result.recommendation == "Agile"]
            traditional_group = [result for result in results if result.recommendation == "Traditional"]
            hybrid_readiness, delivery_strategies, strategy_options = self._strategy_distributions(results)
            evidence_rows = [
                (result.decision_report or {}).get("evidence_scoring", {})
                for result in results
                if (result.decision_report or {}).get("evidence_scoring")
            ]
            documented_rows = [item for item in evidence_rows if int(item.get("confirmed_item_count", 0)) > 0]
            adjusted_score_count = 0
            coverage_totals = {"FLEXIBILITY": 0.0, "PERFORMANCE": 0.0, "STRICTNESS": 0.0}
            for item in documented_rows:
                base_scores = item.get("questionnaire_construct_scores", {})
                decision_scores = item.get("decision_construct_scores", {})
                if any(
                    abs(float(decision_scores.get(key, 0)) - float(base_scores.get(key, 0))) > 0.0001
                    for key in coverage_totals
                ):
                    adjusted_score_count += 1
                for key in coverage_totals:
                    coverage_totals[key] += float(item.get("document_coverage", {}).get(key, 0))
            evidence_adjusted = {
                "documented_assessments": len(documented_rows),
                "assessments_with_score_adjustment": adjusted_score_count,
                "average_coverage": {
                    key: round(value / len(documented_rows), 4) if documented_rows else 0.0
                    for key, value in coverage_totals.items()
                },
                "maximum_construct_contribution": 0.25,
            }

            data = ResearchMetricsData(
                questionnaire_version=selected_questionnaire_version,
                rules_version=selected_rules_version,
                sample_size=len(results),
                cronbach_alpha={
                    "FLEXIBILITY": self._cronbach_alpha(construct_rows["FLEXIBILITY"]),
                    "PERFORMANCE": self._cronbach_alpha(construct_rows["PERFORMANCE"]),
                    "STRICTNESS": self._cronbach_alpha(construct_rows["STRICTNESS"]),
                },
                construct_score_means={
                    "FLEXIBILITY": round(sum(flexibility) / len(flexibility), 4) if flexibility else 0.0,
                    "PERFORMANCE": round(sum(performance) / len(performance), 4) if performance else 0.0,
                    "STRICTNESS": round(sum(strictness) / len(strictness), 4) if strictness else 0.0,
                },
                correlations={
                    "flexibility_vs_agile": self._pearson(flexibility, agile),
                    "performance_vs_agile": self._pearson(performance, agile),
                    "strictness_vs_traditional": self._pearson(strictness, traditional),
                    "agile_vs_traditional": self._pearson(agile, traditional),
                },
                t_tests={
                    "flexibility_agile_vs_traditional": self._welch_t_test(
                        [item.flexibility_score for item in agile_group],
                        [item.flexibility_score for item in traditional_group],
                    ),
                    "performance_agile_vs_traditional": self._welch_t_test(
                        [item.performance_score for item in agile_group],
                        [item.performance_score for item in traditional_group],
                    ),
                    "strictness_agile_vs_traditional": self._welch_t_test(
                        [item.strictness_score for item in agile_group],
                        [item.strictness_score for item in traditional_group],
                    ),
                },
                dependent_variable_means={
                    "overall": self._dependent_variable_means(results),
                    "agile_recommended": self._dependent_variable_means(agile_group),
                    "traditional_recommended": self._dependent_variable_means(traditional_group),
                },
                confidence_distribution=self._confidence_distribution(results),
                risk_flag_counts=self._risk_flag_counts(results),
                hybrid_readiness_distribution=hybrid_readiness,
                delivery_strategy_distribution=delivery_strategies,
                strategy_option_counts=strategy_options,
                evidence_adjusted=evidence_adjusted,
            )
            logger.info("AdminService.get_research_metrics completed sample_size=%s", len(results))
            return GenericResponse.success_response("Research metrics fetched.", data=data)
        except Exception:
            logger.exception("AdminService.get_research_metrics failed unexpectedly.")
            raise ServiceException("Unable to fetch research metrics.") from None
