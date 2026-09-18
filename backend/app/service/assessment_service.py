import json
import logging
import re
import hashlib
import hmac
from datetime import datetime
from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.entity.assessment_entity import (
    AssessmentAnswerEntity,
    AssessmentResultEntity,
    AssessmentSessionEntity,
    AssessmentSubmissionEntity,
)
from app.entity.document_intelligence_entity import DocumentAgentRunEntity, EvidenceAnswerEntity
from app.exceptions.domain_exception import NotFoundException, ServiceException, ValidationException
from app.model.assessment_model import (
    AnswerInput,
    AssessmentCreateRequest,
    AssessmentEventData,
    AssessmentEventRequest,
    AssessmentResultData,
)
from app.model.questionnaire_model import QuestionnairePayload
from app.model.admin_model import RuleConfig
from app.repository.assessment_repository import AssessmentRepository
from app.repository.rule_repository import RuleRepository
from app.service.ai_demo_service import AIDemoService
from app.service.document_intelligence_service import DocumentIntelligenceService
from app.service.engine_service import EngineService
from app.service.questionnaire_service import QuestionnaireService
from app.service.rule_service import RuleService
from app.service.traditional_advisor_service import TraditionalAdvisorService
from app.util.response import GenericResponse

logger = logging.getLogger(__name__)


class AssessmentService:
    DOCUMENT_EVIDENCE_CAP = 0.25
    PROFILE_OPTION_KEY_MAP = {
        "role": "role",
        "industry": "industry",
        "orgSize": "org_size",
        "projectType": "project_type",
        "duration": "duration",
        "teamSize": "team_size",
        "budget": "budget",
    }
    DEPENDENT_KEYS = [
        "timeline_adherence",
        "budget_accuracy",
        "product_quality",
        "user_satisfaction",
        "communication_effectiveness",
        "security_integration",
        "system_integration_effectiveness",
    ]

    def __init__(self):
        self.ai_demo_service = AIDemoService()
        self.document_intelligence_service = DocumentIntelligenceService()
        self.engine = EngineService()
        self.rule_service = RuleService()
        self.questionnaire_service = QuestionnaireService()
        self.traditional_advisor_service = TraditionalAdvisorService()

    @staticmethod
    def normalize_company_name(company: str) -> str:
        normalized_company = re.sub(r"[^\w\s]", "", company.lower().strip())
        return re.sub(r"\s+", " ", normalized_company)

    @staticmethod
    def _get_other_option_label(options: list[str] | None) -> str | None:
        if not options:
            return None
        for option in options:
            if str(option).strip().lower() == "other":
                return option
        return None

    def _validate_profile_options(
        self, payload: AssessmentCreateRequest, questionnaire_payload: QuestionnairePayload
    ) -> dict[str, str]:
        profile_answers = payload.profile.model_dump()
        profile_other_inputs = payload.profile_other_inputs or {}
        allowed_other_keys: set[str] = set()
        cleaned_other_inputs: dict[str, str] = {}
        for question in questionnaire_payload.profile_questions:
            if question.kind != "pill" or not question.options:
                continue
            request_key = self.PROFILE_OPTION_KEY_MAP.get(question.profile_key)
            if not request_key:
                continue
            submitted_value = str(profile_answers.get(request_key, "")).strip()
            other_option_label = self._get_other_option_label(question.options)
            if other_option_label and question.profile_key in profile_other_inputs:
                allowed_other_keys.add(question.profile_key)
            if submitted_value not in question.options:
                raise ValidationException(f"Invalid value for {request_key}.")
            if other_option_label and submitted_value == other_option_label:
                other_value = str(profile_other_inputs.get(question.profile_key, "")).strip()
                if not other_value:
                    raise ValidationException(f"Please specify the other value for {request_key}.")
                cleaned_other_inputs[question.profile_key] = other_value
                continue
            if question.profile_key in profile_other_inputs:
                raise ValidationException(f"Unexpected custom value for {request_key}.")
        unexpected_keys = set(profile_other_inputs) - allowed_other_keys
        if unexpected_keys:
            raise ValidationException("Unexpected custom values were submitted.")
        return cleaned_other_inputs

    @staticmethod
    def _validate_likert_answers(
        answers: list[AnswerInput], questionnaire_payload: QuestionnairePayload
    ) -> None:
        expected = {
            question.question_id: question.construct_key
            for question in questionnaire_payload.likert_questions
        }
        submitted_keys = [answer.question_key for answer in answers]
        if len(submitted_keys) != len(set(submitted_keys)):
            raise ValidationException("Each methodology question must be answered exactly once.")
        if set(submitted_keys) != set(expected):
            missing = sorted(set(expected) - set(submitted_keys))
            unexpected = sorted(set(submitted_keys) - set(expected))
            details: list[str] = []
            if missing:
                details.append(f"missing: {', '.join(missing)}")
            if unexpected:
                details.append(f"unexpected: {', '.join(unexpected)}")
            raise ValidationException(f"Submitted methodology answers do not match the questionnaire ({'; '.join(details)}).")
        for answer in answers:
            if answer.construct_key != expected[answer.question_key]:
                raise ValidationException(f"Construct does not match questionnaire for {answer.question_key}.")

    def _resolve_draft(
        self, repo: AssessmentRepository, draft_session_id: str | None, participant_token: str | None
    ):
        if not draft_session_id:
            return None
        draft = repo.get_draft_by_session_id(draft_session_id)
        if not draft:
            raise ValidationException("Draft not found.")
        token_hash = hashlib.sha256(participant_token.encode("utf-8")).hexdigest() if participant_token else ""
        if draft.participant_token_hash and not hmac.compare_digest(draft.participant_token_hash, token_hash):
            raise ValidationException("Assessment session is not available in this browser.")
        if draft.status == "submitted":
            raise ValidationException("Draft has already been submitted.")
        draft.status = "submitted"
        repo.save_draft(draft)
        return draft

    def _evidence_scoring(
        self,
        db: Session,
        draft,
        questionnaire: QuestionnairePayload,
        questionnaire_construct_scores: dict[str, float],
    ) -> tuple[dict[str, object], list[EvidenceAnswerEntity]]:
        """Blend confirmed document-only evidence without treating missing evidence as neutral."""
        constructs = ("FLEXIBILITY", "PERFORMANCE", "STRICTNESS")
        questions_by_key = {item.question_id: item for item in questionnaire.document_questions}
        configured_weights = {
            construct: sum(
                float(question.weight)
                for question in questionnaire.document_questions
                if question.construct_key == construct
            )
            for construct in constructs
        }
        evidence_answers = (
            list(db.scalars(select(EvidenceAnswerEntity).where(EvidenceAnswerEntity.draft_id == draft.id)))
            if draft
            else []
        )
        confirmed: dict[str, list[tuple[float, float]]] = {construct: [] for construct in constructs}
        for answer in evidence_answers:
            question = questions_by_key.get(answer.question_key)
            if not question or answer.final_source != "confirmed_document" or answer.final_value not in {"1", "2", "3", "4", "5"}:
                continue
            confirmed[question.construct_key].append((float(question.weight), float(answer.final_value)))

        document_scores: dict[str, float | None] = {}
        coverage: dict[str, float] = {}
        contribution: dict[str, float] = {}
        decision_scores: dict[str, float] = {}
        for construct in constructs:
            responses = confirmed[construct]
            response_weight = sum(weight for weight, _ in responses)
            coverage_value = round(response_weight / configured_weights[construct], 4) if configured_weights[construct] else 0.0
            document_score = (
                round(sum(weight * value for weight, value in responses) / response_weight, 4)
                if response_weight
                else None
            )
            contribution_value = round(self.DOCUMENT_EVIDENCE_CAP * coverage_value, 4)
            questionnaire_score = float(questionnaire_construct_scores[construct])
            decision_scores[construct] = (
                questionnaire_score
                if document_score is None
                else round(
                    (questionnaire_score * (1 - contribution_value)) + (document_score * contribution_value),
                    4,
                )
            )
            document_scores[construct] = document_score
            coverage[construct] = coverage_value
            contribution[construct] = contribution_value

        return (
            {
                "questionnaire_construct_scores": {
                    key: round(float(value), 4) for key, value in questionnaire_construct_scores.items()
                },
                "document_construct_scores": document_scores,
                "document_coverage": coverage,
                "document_contribution": contribution,
                "decision_construct_scores": decision_scores,
                "document_evidence_cap": self.DOCUMENT_EVIDENCE_CAP,
                "confirmed_item_count": sum(len(items) for items in confirmed.values()),
            },
            evidence_answers,
        )

    def track_event(self, db: Session, payload: AssessmentEventRequest) -> GenericResponse[AssessmentEventData]:
        try:
            repo = AssessmentRepository(db)
            session = repo.get_session_by_session_id(payload.session_id)
            if not session:
                session = repo.create_session(
                    AssessmentSessionEntity(
                        session_id=payload.session_id,
                        opened_at=datetime.utcnow(),
                        status="opened",
                        answered_count=0,
                    )
                )
            if payload.event == "question_answered":
                if payload.question_index is None:
                    raise ValidationException("question_index is required for question_answered events.")
                session.answered_count = max(int(session.answered_count), int(payload.question_index))
                session.last_question_key = payload.question_key
                session.status = "in_progress"
                repo.save_session(session)
            data = AssessmentEventData(
                session_id=session.session_id,
                status=session.status,
                answered_count=session.answered_count,
            )
            db.commit()
            return GenericResponse.success_response("Assessment event tracked.", data=data, status_code=HTTPStatus.CREATED)
        except ValidationException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            logger.exception("AssessmentService.track_event failed unexpectedly.")
            raise ServiceException("Unable to track assessment event.") from None

    def create_assessment(
        self, db: Session, payload: AssessmentCreateRequest, participant_token: str | None = None
    ) -> GenericResponse[AssessmentResultData]:
        logger.info("AssessmentService.create_assessment started.")
        try:
            if not payload.answers:
                raise ValidationException("At least one answer is required.")

            repo = AssessmentRepository(db)
            draft = self._resolve_draft(repo, payload.draft_id, participant_token)
            active_questionnaire = self.questionnaire_service.get_active(db)
            questionnaire_payload = QuestionnairePayload(
                **json.loads(draft.questionnaire_snapshot if draft and draft.questionnaire_snapshot else active_questionnaire.payload_json)
            )
            self._validate_likert_answers(payload.answers, questionnaire_payload)
            profile_other_inputs = self._validate_profile_options(payload, questionnaire_payload)
            normalized_company = self.normalize_company_name(payload.profile.company)
            draft_id = draft.id if draft else None
            session = repo.get_session_by_session_id(payload.session_id) if payload.session_id else None

            submission = repo.create_submission(
                AssessmentSubmissionEntity(
                    name=payload.profile.name,
                    role=payload.profile.role,
                    company=payload.profile.company,
                    normalized_company=normalized_company,
                    profile_other_inputs=profile_other_inputs or None,
                    draft_id=draft_id,
                    industry=payload.profile.industry,
                    org_size=payload.profile.org_size,
                    project_name=payload.profile.project_name,
                    project_type=payload.profile.project_type,
                    duration=payload.profile.duration,
                    team_size=payload.profile.team_size,
                    budget=payload.profile.budget,
                )
            )
            if session:
                session.completed_at = datetime.utcnow()
                session.status = "completed"
                session.answered_count = max(
                    int(session.answered_count),
                    len(questionnaire_payload.profile_questions) + len(questionnaire_payload.likert_questions),
                )
                session.submission_id = submission.id
                repo.save_session(session)

            for answer in payload.answers:
                repo.create_answer(
                    AssessmentAnswerEntity(
                        submission_id=submission.id,
                        question_key=answer.question_key,
                        construct=answer.construct_key,
                        value=answer.value,
                    )
                )

            active_rule = self.rule_service.get_active_rule(db)
            parsed_rule = (
                self.rule_service._with_defaults(RuleConfig(**json.loads(draft.rule_snapshot)))
                if draft and draft.rule_snapshot
                else self.rule_service.parse_rule(active_rule)
            )
            rules_version = draft.rule_version if draft and draft.rule_version else active_rule.version
            questionnaire_version = draft.questionnaire_version if draft and draft.questionnaire_version else active_questionnaire.version
            questionnaire_computed = self.engine.compute(payload.answers, parsed_rule)
            evidence_scoring, stored_evidence_answers = self._evidence_scoring(
                db=db,
                draft=draft,
                questionnaire=questionnaire_payload,
                questionnaire_construct_scores=questionnaire_computed.construct_scores,
            )
            computed = self.engine.compute_from_construct_scores(
                evidence_scoring["decision_construct_scores"], parsed_rule
            )
            dependent_scores = self._dependent_scores(computed.construct_scores, parsed_rule)
            agile_series = self._dependent_scores(parsed_rule.agile_baseline, parsed_rule)
            traditional_series = self._dependent_scores(parsed_rule.traditional_baseline, parsed_rule)
            draft_documents = repo.list_documents_for_draft(draft_id) if draft_id else []
            score_gap = round(abs(float(computed.agile_score) - float(computed.traditional_score)), 2)
            comparison_series = {
                "dimensions": self.DEPENDENT_KEYS,
                "project": [dependent_scores[key] for key in self.DEPENDENT_KEYS],
                "agile": [agile_series[key] for key in self.DEPENDENT_KEYS],
                "traditional": [traditional_series[key] for key in self.DEPENDENT_KEYS],
            }
            insights = self._insights(
                recommendation=computed.recommendation,
                agile_score=computed.agile_score,
                traditional_score=computed.traditional_score,
                dependent_scores=dependent_scores,
            )
            decision_report = self._decision_report(
                recommendation=computed.recommendation,
                agile_score=computed.agile_score,
                traditional_score=computed.traditional_score,
                construct_scores=computed.construct_scores,
                dependent_scores=dependent_scores,
                insights=insights,
                rules=parsed_rule,
                profile=payload.profile,
            )
            decision_report["evidence_scoring"] = evidence_scoring
            if draft_id:
                agent_runs = list(
                    db.scalars(
                        select(DocumentAgentRunEntity)
                        .where(DocumentAgentRunEntity.draft_id == draft_id)
                        .order_by(DocumentAgentRunEntity.created_at.asc())
                    )
                )
                if agent_runs:
                    ai_demo_trace = [
                        {
                            "stage": "evidence",
                            "label": f"Evidence extraction: {run.question_key or 'document'}",
                            "status": run.status,
                            "detail": f"Retrieved and validated cited evidence in {int(run.trace_json.get('iterations', 0))} iteration(s).",
                            "artifacts": {
                                "retrieved_chunk_ids": run.trace_json.get("retrieved_chunk_ids", []),
                                "candidate_valid": run.trace_json.get("candidate_valid", False),
                            },
                            "duration_ms": run.duration_ms,
                        }
                        for run in agent_runs
                    ]
                    ai_demo_summary = {
                        "documents_processed": len([document for document in draft_documents if document.status == "processed"]),
                        "trace_steps": len(agent_runs),
                        "candidate_signals": [
                            {
                                "key": answer.question_key,
                                "label": answer.question_key,
                                "value": answer.final_value or answer.proposed_value or "not available",
                                "confidence": answer.confidence,
                                "source": answer.final_source or answer.evidence_status,
                            }
                            for answer in stored_evidence_answers
                        ],
                        "document_filenames": [document.filename for document in draft_documents],
                        "demo_mode": False,
                        "explanation_scope": "cited_evidence_and_confirmed_answers",
                    }
                else:
                    ai_demo_trace, ai_demo_summary = self.ai_demo_service.build_trace(
                        profile=payload.profile,
                        documents=draft_documents,
                        construct_scores=computed.construct_scores,
                        recommendation=computed.recommendation,
                        score_gap=score_gap,
                    )
            else:
                ai_demo_trace, ai_demo_summary = self.ai_demo_service.build_trace(
                    profile=payload.profile,
                    documents=draft_documents,
                    construct_scores=computed.construct_scores,
                    recommendation=computed.recommendation,
                    score_gap=score_gap,
                )
            result = repo.create_result(
                AssessmentResultEntity(
                    submission_id=submission.id,
                    recommendation=computed.recommendation,
                    agile_score=computed.agile_score,
                    traditional_score=computed.traditional_score,
                    flexibility_score=questionnaire_computed.construct_scores["FLEXIBILITY"],
                    performance_score=questionnaire_computed.construct_scores["PERFORMANCE"],
                    strictness_score=questionnaire_computed.construct_scores["STRICTNESS"],
                    rationale=computed.rationale,
                    dependent_variable_scores=dependent_scores,
                    comparison_series=comparison_series,
                    decision_report=decision_report,
                    ai_demo_trace=ai_demo_trace,
                    ai_demo_summary=ai_demo_summary,
                    rules_version=rules_version,
                    questionnaire_version=questionnaire_version,
                )
            )
            evidence_answers = (
                self.document_intelligence_service.list_evidence_answers(db, draft.session_id).data or []
                if draft and draft_id
                else []
            )
            try:
                traditional_advisor = self.traditional_advisor_service.queue_for_result(db, submission, result)
            except Exception:
                logger.exception("Unable to queue traditional advisor submission_id=%s", submission.id)
                traditional_advisor = None
            data = AssessmentResultData(
                submission_id=submission.id,
                recommendation=computed.recommendation,
                agile_score=computed.agile_score,
                traditional_score=computed.traditional_score,
                construct_scores=computed.construct_scores,
                evidence_scoring=evidence_scoring,
                dependent_variable_scores=dependent_scores,
                comparison_series=comparison_series,
                insights=insights,
                decision_report=decision_report,
                ai_demo_trace=ai_demo_trace,
                ai_demo_summary=ai_demo_summary,
                evidence_answers=evidence_answers,
                traditional_advisor=traditional_advisor,
                rationale=computed.rationale,
                rules_version=rules_version,
                questionnaire_version=questionnaire_version,
                created_at=result.created_at,
            )
            return GenericResponse.success_response(
                "Assessment completed successfully.", data=data, status_code=HTTPStatus.CREATED
            )
        except ValidationException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            logger.exception("AssessmentService.create_assessment failed unexpectedly.")
            raise ServiceException() from None

    def get_assessment(self, db: Session, submission_id: int) -> GenericResponse[AssessmentResultData]:
        try:
            repo = AssessmentRepository(db)
            result = repo.get_result_by_submission_id(submission_id)
            if not result:
                raise NotFoundException("Submission not found.")
            submission = repo.get_submission_by_id(submission_id)
            questionnaire_construct_scores = {
                "FLEXIBILITY": result.flexibility_score,
                "PERFORMANCE": result.performance_score,
                "STRICTNESS": result.strictness_score,
            }
            stored_rule = RuleRepository(db).get_by_version(result.rules_version)
            parsed_rule = self.rule_service.parse_rule(stored_rule or self.rule_service.get_active_rule(db))
            stored_report = result.decision_report or {}
            evidence_scoring = stored_report.get("evidence_scoring", {})
            construct_scores = evidence_scoring.get("decision_construct_scores", questionnaire_construct_scores)
            dependent_scores = result.dependent_variable_scores or self._dependent_scores(
                construct_scores, parsed_rule
            )
            comparison_series = result.comparison_series or {
                "dimensions": self.DEPENDENT_KEYS,
                "project": [dependent_scores[key] for key in self.DEPENDENT_KEYS],
                "agile": [],
                "traditional": [],
            }
            insights = self._insights(
                recommendation=result.recommendation,
                agile_score=result.agile_score,
                traditional_score=result.traditional_score,
                dependent_scores=dependent_scores,
            )
            decision_report = stored_report or self._decision_report(
                recommendation=result.recommendation,
                agile_score=result.agile_score,
                traditional_score=result.traditional_score,
                construct_scores=construct_scores,
                dependent_scores=dependent_scores,
                insights=insights,
                rules=parsed_rule,
                profile=submission,
            )
            if "evidence_scoring" not in decision_report:
                evidence_scoring = {
                    "questionnaire_construct_scores": questionnaire_construct_scores,
                    "document_construct_scores": {key: None for key in questionnaire_construct_scores},
                    "document_coverage": {key: 0.0 for key in questionnaire_construct_scores},
                    "document_contribution": {key: 0.0 for key in questionnaire_construct_scores},
                    "decision_construct_scores": construct_scores,
                    "document_evidence_cap": self.DOCUMENT_EVIDENCE_CAP,
                    "confirmed_item_count": 0,
                }
                decision_report = {**decision_report, "evidence_scoring": evidence_scoring}
            if "strategy_profile" not in decision_report:
                decision_report = {
                    **decision_report,
                    "strategy_profile": self._strategy_profile(
                        recommendation=result.recommendation,
                        agile_score=result.agile_score,
                        traditional_score=result.traditional_score,
                        construct_scores=construct_scores,
                        profile=submission,
                    ),
                }
            ai_demo_trace = result.ai_demo_trace or []
            ai_demo_summary = result.ai_demo_summary or {
                "documents_processed": 0,
                "trace_steps": len(ai_demo_trace),
                "candidate_signals": [],
                "document_filenames": [],
                "demo_mode": True,
                "explanation_scope": "candidate_signals_only",
            }
            data = AssessmentResultData(
                submission_id=submission_id,
                recommendation=result.recommendation,
                agile_score=result.agile_score,
                traditional_score=result.traditional_score,
                construct_scores=construct_scores,
                evidence_scoring=evidence_scoring,
                dependent_variable_scores=dependent_scores,
                comparison_series=comparison_series,
                insights=insights,
                decision_report=decision_report,
                ai_demo_trace=ai_demo_trace,
                ai_demo_summary=ai_demo_summary,
                evidence_answers=[],
                # Advisory content is intentionally only decrypted through the participant-cookie or admin endpoint.
                traditional_advisor=None,
                rationale=result.rationale,
                rules_version=result.rules_version,
                questionnaire_version=result.questionnaire_version,
                created_at=result.created_at,
            )
            return GenericResponse.success_response("Assessment fetched.", data=data)
        except NotFoundException:
            raise
        except Exception:
            logger.exception("AssessmentService.get_assessment failed unexpectedly.")
            raise ServiceException() from None

    @staticmethod
    def _dependent_scores(construct_scores: dict[str, float], rules) -> dict[str, float]:
        scores: dict[str, float] = {}
        for key, weights in rules.dependent_variable_rules.items():
            total_weight = sum(float(weight) for weight in weights.values())
            if total_weight == 0:
                scores[key] = 0.0
                continue
            total = sum(float(construct_scores[construct]) * float(weight) for construct, weight in weights.items())
            scores[key] = round(total / total_weight, 4)
        return scores

    def _insights(
        self,
        recommendation: str,
        agile_score: float,
        traditional_score: float,
        dependent_scores: dict[str, float],
    ) -> dict[str, str | float]:
        strongest = max(dependent_scores.items(), key=lambda item: item[1])
        weakest = min(dependent_scores.items(), key=lambda item: item[1])
        score_gap = round(abs(agile_score - traditional_score), 2)
        confidence = (
            "high" if score_gap >= 20 else "moderate" if score_gap >= 10 else "close"
        )
        return {
            "recommended_direction": recommendation,
            "strongest_dimension": strongest[0],
            "strongest_score": strongest[1],
            "weakest_dimension": weakest[0],
            "weakest_score": weakest[1],
            "score_gap": score_gap,
            "confidence_level": confidence,
        }

    def _decision_report(
        self,
        recommendation: str,
        agile_score: float,
        traditional_score: float,
        construct_scores: dict[str, float],
        dependent_scores: dict[str, float],
        insights: dict[str, str | float],
        rules,
        profile,
    ) -> dict[str, object]:
        score_gap = float(insights["score_gap"])
        return {
            "recommendation": recommendation,
            "confidence_level": insights["confidence_level"],
            "score_gap": score_gap,
            "methodology_fit_summary": rules.explanation_templates.get(recommendation, ""),
            "outcome_scores": dependent_scores,
            "drivers": self._drivers(construct_scores=construct_scores, rules=rules),
            "risk_flags": self._risk_flags(
                construct_scores=construct_scores,
                agile_score=agile_score,
                traditional_score=traditional_score,
                rules=rules,
            ),
            "tradeoffs": self._tradeoffs(recommendation=recommendation, dependent_scores=dependent_scores),
            "hypothesis_evidence": self._hypothesis_evidence(
                dependent_scores=dependent_scores,
                agile_score=agile_score,
                traditional_score=traditional_score,
            ),
            "strategy_profile": self._strategy_profile(
                recommendation=recommendation,
                agile_score=agile_score,
                traditional_score=traditional_score,
                construct_scores=construct_scores,
                profile=profile,
            ),
            "next_steps": rules.next_step_templates.get(recommendation, []),
            "limitations": [
                "This is a rule-based decision-support output, not a project guarantee.",
                "The model evaluates Agile and Traditional as binary research categories.",
                "Results depend on self-reported project inputs at this point in time.",
            ],
        }

    @staticmethod
    def _drivers(construct_scores: dict[str, float], rules) -> list[dict[str, object]]:
        drivers: list[dict[str, object]] = []
        for key, rule in rules.driver_rules.items():
            construct = str(rule.get("construct", ""))
            if construct not in construct_scores:
                continue
            value = float(construct_scores[construct])
            threshold = float(rule.get("threshold", 0))
            if value >= threshold:
                drivers.append(
                    {
                        "key": key,
                        "label": str(rule.get("label", key)),
                        "methodology": str(rule.get("methodology", "")),
                        "construct": construct,
                        "score": round(value, 2),
                    }
                )
        return drivers

    @staticmethod
    def _risk_flags(
        construct_scores: dict[str, float],
        agile_score: float,
        traditional_score: float,
        rules,
    ) -> list[dict[str, object]]:
        flags: list[dict[str, object]] = []
        metrics = {
            "score_gap": abs(agile_score - traditional_score),
            "agile_score": agile_score,
            "traditional_score": traditional_score,
            **construct_scores,
        }
        for key, rule in rules.risk_flag_rules.items():
            metric_name = str(rule.get("metric") or rule.get("construct") or "")
            if metric_name not in metrics:
                continue
            value = float(metrics[metric_name])
            threshold = float(rule.get("threshold", 0))
            operator = str(rule.get("operator", "gte"))
            triggered = value >= threshold if operator == "gte" else value <= threshold
            if triggered:
                flags.append(
                    {
                        "key": key,
                        "label": str(rule.get("label", key)),
                        "metric": metric_name,
                        "value": round(value, 2),
                    }
                )
        return flags

    @staticmethod
    def _tradeoffs(recommendation: str, dependent_scores: dict[str, float]) -> dict[str, list[str]]:
        weakest = sorted(dependent_scores.items(), key=lambda item: item[1])[:2]
        strengths = sorted(dependent_scores.items(), key=lambda item: item[1], reverse=True)[:2]
        return {
            "strengths": [f"{key.replace('_', ' ').title()} is a strong fit ({value:.2f}/5)." for key, value in strengths],
            "watch_areas": [f"{key.replace('_', ' ').title()} needs management attention ({value:.2f}/5)." for key, value in weakest],
            "methodology_note": [
                "Agile improves adaptation and feedback but needs active stakeholder involvement."
                if recommendation == "Agile"
                else "Traditional improves control and documentation but can be slower to adapt to change."
            ],
        }

    @staticmethod
    def _hypothesis_evidence(
        dependent_scores: dict[str, float],
        agile_score: float,
        traditional_score: float,
    ) -> dict[str, dict[str, object]]:
        return {
            "H1": {
                "label": "Timeline adherence differs by methodology fit.",
                "score": dependent_scores["timeline_adherence"],
            },
            "H2": {
                "label": "Agile is expected to improve user satisfaction when adaptability is high.",
                "score": dependent_scores["user_satisfaction"],
            },
            "H3": {
                "label": "Traditional is expected to perform better in security-sensitive environments.",
                "score": dependent_scores["security_integration"],
            },
            "H4": {
                "label": "Methodology choice influences system integration effectiveness.",
                "score": dependent_scores["system_integration_effectiveness"],
            },
            "H5": {
                "label": "Methodology fit relates to overall IS project success.",
                "score": round(max(agile_score, traditional_score), 2),
            },
        }

    @staticmethod
    def _profile_value(profile, key: str) -> str:
        if profile is None:
            return ""
        return str(getattr(profile, key, "") or "")

    @classmethod
    def _has_complexity_signal(cls, profile) -> bool:
        project_type = cls._profile_value(profile, "project_type").lower()
        team_size = cls._profile_value(profile, "team_size")
        org_size = cls._profile_value(profile, "org_size")
        return (
            "system integration" in project_type
            or "upgrade" in project_type
            or "migration" in project_type
            or "16" in team_size
            or "30" in team_size
            or "201" in org_size
            or "1,000" in org_size
        )

    @classmethod
    def _strategy_profile(
        cls,
        recommendation: str,
        agile_score: float,
        traditional_score: float,
        construct_scores: dict[str, float],
        profile,
    ) -> dict[str, object]:
        flexibility = float(construct_scores.get("FLEXIBILITY", 0.0))
        performance = float(construct_scores.get("PERFORMANCE", 0.0))
        strictness = float(construct_scores.get("STRICTNESS", 0.0))
        score_gap = abs(float(agile_score) - float(traditional_score))
        complexity = cls._has_complexity_signal(profile)
        hybrid_score = round(
            max(0.0, 1 - score_gap / 40) * 40
            + (min(flexibility, strictness) / 5) * 25
            + (performance / 5) * 15
            + (20 if complexity else 0)
        )
        hybrid_score = min(100, max(0, hybrid_score))
        hybrid_level = "high" if hybrid_score >= 70 else "moderate" if hybrid_score >= 45 else "low"

        if hybrid_level == "high" and recommendation == "Agile":
            delivery_strategy = "agile_led_with_governance"
        elif hybrid_level == "high" and recommendation == "Traditional":
            delivery_strategy = "traditional_led_with_iterative_validation"
        elif hybrid_level == "moderate":
            delivery_strategy = "primary_with_targeted_practices"
        elif recommendation == "Agile":
            delivery_strategy = "adaptive_agile"
        else:
            delivery_strategy = "predictive_traditional"

        project_type = cls._profile_value(profile, "project_type").lower()
        options: list[dict[str, str]] = []
        if flexibility >= 3.8 and strictness < 3.8:
            options.append(
                {
                    "key": "scrum",
                    "label": "Scrum",
                    "fit": "High",
                    "reason": "Frequent stakeholder feedback and requirement change favor time-boxed iterative delivery.",
                }
            )
        if performance >= 3.8 or "maintenance" in project_type:
            options.append(
                {
                    "key": "kanban",
                    "label": "Kanban",
                    "fit": "Medium",
                    "reason": "Flow control helps manage delivery pressure, support work, and visible work-in-progress.",
                }
            )
        if strictness >= 3.8 and performance >= 3.5 and flexibility >= 3.0:
            options.append(
                {
                    "key": "prince2_agile",
                    "label": "PRINCE2 Agile",
                    "fit": "Medium",
                    "reason": "Governance pressure is high, but iterative validation can still reduce delivery risk.",
                }
            )
        if hybrid_score >= 45:
            options.append(
                {
                    "key": "disciplined_agile",
                    "label": "Disciplined Agile",
                    "fit": "Medium",
                    "reason": "The project has mixed constraints that benefit from context-driven way-of-working selection.",
                }
            )
        if complexity:
            options.append(
                {
                    "key": "safe",
                    "label": "SAFe",
                    "fit": "Selective",
                    "reason": "Large team, organization, or integration signals may require cross-team coordination practices.",
                }
            )
        if not options:
            options.append(
                {
                    "key": recommendation.lower(),
                    "label": recommendation,
                    "fit": "Core",
                    "reason": "The validated Agile vs Traditional result is the strongest guidance for this profile.",
                }
            )

        governance_controls = [
            "Keep the Agile vs Traditional score as the validated decision baseline.",
        ]
        if strictness >= 3.8:
            governance_controls.append("Define security, compliance, and integration approval gates before delivery starts.")
        if performance >= 3.8:
            governance_controls.append("Track timeline and budget variance through milestone reviews.")
        if score_gap < 10:
            governance_controls.append("Run a stakeholder review before committing because the methodology fit is close.")
        if flexibility >= 3.8:
            governance_controls.append("Schedule recurring feedback checkpoints to absorb requirement change.")

        rationale = [
            f"Agile and Traditional score gap is {score_gap:.1f}.",
            f"Flexibility {flexibility:.2f}, performance {performance:.2f}, strictness {strictness:.2f}.",
        ]
        if complexity:
            rationale.append("Project profile includes integration, scale, or migration complexity.")

        return {
            "hybrid_readiness": {
                "score": hybrid_score,
                "level": hybrid_level,
                "rationale": rationale,
            },
            "delivery_strategy": delivery_strategy,
            "strategy_options": options,
            "governance_controls": governance_controls,
            "research_boundary_note": (
                "Only Agile vs Traditional is empirically validated in the current MethodAlign research. "
                "These strategy options are advisory practices, not replacement recommendations."
            ),
        }
