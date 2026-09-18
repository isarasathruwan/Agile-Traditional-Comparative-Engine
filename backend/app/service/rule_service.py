import json
import logging
from http import HTTPStatus

from sqlalchemy.orm import Session

from app.entity.rule_config_entity import RuleConfigVersionEntity
from app.exceptions.domain_exception import NotFoundException, ServiceException, ValidationException
from app.model.admin_model import RuleConfig, RuleConfigData, RuleConfigUpdateRequest, RulePreviewData
from app.model.assessment_model import AnswerInput
from app.repository.rule_repository import RuleRepository
from app.service.engine_service import EngineService
from app.util.response import GenericResponse

logger = logging.getLogger(__name__)


DEFAULT_RULES = RuleConfig(
    construct_weights={"FLEXIBILITY": 1.37, "PERFORMANCE": 0.64, "STRICTNESS": 0.99},
    agile_baseline={"FLEXIBILITY": 4.06, "PERFORMANCE": 3.33, "STRICTNESS": 2.92},
    traditional_baseline={"FLEXIBILITY": 2.14, "PERFORMANCE": 4.44, "STRICTNESS": 4.44},
    strictness_threshold=3.8,
    strictness_override_enabled=False,
    compatibility_normalization="weighted_range",
    dependent_variable_rules={
        "timeline_adherence": {"PERFORMANCE": 1.0},
        "budget_accuracy": {"PERFORMANCE": 1.0},
        "product_quality": {"PERFORMANCE": 0.5, "STRICTNESS": 0.5},
        "user_satisfaction": {"FLEXIBILITY": 1.0},
        "communication_effectiveness": {"FLEXIBILITY": 1.0},
        "security_integration": {"STRICTNESS": 1.0},
        "system_integration_effectiveness": {"STRICTNESS": 1.0},
    },
    driver_rules={
        "requirements_change": {
            "construct": "FLEXIBILITY",
            "methodology": "Agile",
            "threshold": 3.8,
            "label": "Strong adaptation and iterative-readiness signal",
        },
        "delivery_control": {
            "construct": "PERFORMANCE",
            "methodology": "Traditional",
            "threshold": 3.8,
            "label": "Strong delivery-constraint pressure",
        },
        "security_control": {
            "construct": "STRICTNESS",
            "methodology": "Traditional",
            "threshold": 3.8,
            "label": "Strong assurance and dependency pressure",
        },
    },
    risk_flag_rules={
        "close_call": {
            "metric": "score_gap",
            "operator": "lte",
            "threshold": 10,
            "label": "Recommendation is close; review tradeoffs before committing.",
        },
        "security_sensitive": {
            "construct": "STRICTNESS",
            "operator": "gte",
            "threshold": 3.8,
            "label": "Assurance, traceability, or dependency controls need explicit planning.",
        },
        "low_adaptability": {
            "construct": "FLEXIBILITY",
            "operator": "lte",
            "threshold": 2.5,
            "label": "Low adaptability may limit iterative delivery benefits.",
        },
    },
    explanation_templates={
        "Agile": "The project profile is closer to the survey-informed Agile reference where adaptation and iterative-delivery readiness are stronger.",
        "Traditional": "The project profile is closer to the survey-informed Traditional reference where delivery constraints, assurance, and dependency control are stronger.",
    },
    next_step_templates={
        "Agile": [
            "Confirm stakeholder availability for frequent reviews.",
            "Define short iteration goals and feedback checkpoints.",
            "Track scope changes openly so budget and timeline impact stays visible.",
        ],
        "Traditional": [
            "Lock critical requirements and approval gates before implementation.",
            "Document security, compliance, and integration dependencies early.",
            "Use milestone reviews to control timeline and budget variance.",
        ],
    },
)


class RuleService:
    SAMPLE_ANSWERS = [
        {
            "name": "Dynamic Project",
            "answers": [
                {"question_key": "Q11", "construct": "FLEXIBILITY", "value": 5},
                {"question_key": "Q12", "construct": "FLEXIBILITY", "value": 5},
                {"question_key": "Q13", "construct": "FLEXIBILITY", "value": 4},
                {"question_key": "Q14", "construct": "FLEXIBILITY", "value": 5},
                {"question_key": "Q15", "construct": "PERFORMANCE", "value": 2},
                {"question_key": "Q16", "construct": "PERFORMANCE", "value": 2},
                {"question_key": "Q17", "construct": "PERFORMANCE", "value": 2},
                {"question_key": "Q18", "construct": "STRICTNESS", "value": 2},
                {"question_key": "Q19", "construct": "STRICTNESS", "value": 2},
                {"question_key": "Q20", "construct": "STRICTNESS", "value": 2},
                {"question_key": "Q21", "construct": "STRICTNESS", "value": 2},
                {"question_key": "Q22", "construct": "STRICTNESS", "value": 2},
            ],
        },
        {
            "name": "Control Heavy Project",
            "answers": [
                {"question_key": "Q11", "construct": "FLEXIBILITY", "value": 2},
                {"question_key": "Q12", "construct": "FLEXIBILITY", "value": 2},
                {"question_key": "Q13", "construct": "FLEXIBILITY", "value": 2},
                {"question_key": "Q14", "construct": "FLEXIBILITY", "value": 2},
                {"question_key": "Q15", "construct": "PERFORMANCE", "value": 5},
                {"question_key": "Q16", "construct": "PERFORMANCE", "value": 5},
                {"question_key": "Q17", "construct": "PERFORMANCE", "value": 5},
                {"question_key": "Q18", "construct": "STRICTNESS", "value": 5},
                {"question_key": "Q19", "construct": "STRICTNESS", "value": 5},
                {"question_key": "Q20", "construct": "STRICTNESS", "value": 5},
                {"question_key": "Q21", "construct": "STRICTNESS", "value": 5},
                {"question_key": "Q22", "construct": "STRICTNESS", "value": 5},
            ],
        },
    ]

    @staticmethod
    def _confidence_level(agile_score: float, traditional_score: float) -> str:
        score_gap = abs(float(agile_score) - float(traditional_score))
        if score_gap >= 20:
            return "high"
        if score_gap >= 10:
            return "moderate"
        return "close"

    @staticmethod
    def _with_defaults(payload: RuleConfig) -> RuleConfig:
        data = DEFAULT_RULES.model_dump()
        incoming = payload.model_dump()
        for key, value in incoming.items():
            data[key] = value or data[key]
        return RuleConfig(**data)

    def _validate(self, payload: RuleConfig) -> None:
        keys = {"FLEXIBILITY", "PERFORMANCE", "STRICTNESS"}
        if set(payload.construct_weights.keys()) != keys:
            raise ValidationException("construct_weights must include FLEXIBILITY, PERFORMANCE, STRICTNESS")
        if any(weight <= 0 for weight in payload.construct_weights.values()):
            raise ValidationException("construct_weights must all be greater than zero")
        if set(payload.agile_baseline.keys()) != keys:
            raise ValidationException("agile_baseline must include FLEXIBILITY, PERFORMANCE, STRICTNESS")
        if set(payload.traditional_baseline.keys()) != keys:
            raise ValidationException("traditional_baseline must include FLEXIBILITY, PERFORMANCE, STRICTNESS")
        if set(payload.dependent_variable_rules.keys()) != set(DEFAULT_RULES.dependent_variable_rules.keys()):
            raise ValidationException("dependent_variable_rules must include all seven decision-signal dimensions")

    def get_active_rule(self, db: Session) -> RuleConfigVersionEntity:
        repository = RuleRepository(db)
        active = repository.get_active()
        if active:
            return active
        seed = RuleConfigVersionEntity(version=1, payload_json=DEFAULT_RULES.model_dump_json(), is_active=True)
        return repository.create(seed)

    def parse_rule(self, row: RuleConfigVersionEntity) -> RuleConfig:
        raw = json.loads(row.payload_json)
        payload = DEFAULT_RULES.model_dump()
        payload.update(raw)
        if "strictness_override_enabled" not in raw:
            payload["strictness_override_enabled"] = True
        if "compatibility_normalization" not in raw:
            payload["compatibility_normalization"] = "legacy_fixed_15"
        return RuleConfig(**payload)

    def get_rule_payload(self, db: Session) -> GenericResponse[RuleConfigData]:
        try:
            active = self.get_active_rule(db)
            data = RuleConfigData(
                version=active.version,
                payload=self.parse_rule(active),
                changed_by=active.changed_by,
                change_note=active.change_note,
                created_at=active.created_at.isoformat(),
            )
            return GenericResponse.success_response("Active rules fetched.", data=data)
        except Exception:
            logger.exception("RuleService.get_rule_payload failed unexpectedly.")
            raise ServiceException() from None

    def _to_data(self, row: RuleConfigVersionEntity) -> RuleConfigData:
        return RuleConfigData(
            version=row.version,
            payload=self.parse_rule(row),
            changed_by=row.changed_by,
            change_note=row.change_note,
            created_at=row.created_at.isoformat(),
        )

    def update_rule_payload(
        self, db: Session, payload: RuleConfigUpdateRequest, changed_by: str
    ) -> GenericResponse[RuleConfigData]:
        try:
            rule_payload = self._with_defaults(payload.payload)
            self._validate(rule_payload)
            repository = RuleRepository(db)
            active = self.get_active_rule(db)
            repository.deactivate(active)
            next_version = repository.get_latest_version() + 1
            row = RuleConfigVersionEntity(
                version=next_version,
                payload_json=json.dumps(rule_payload.model_dump()),
                is_active=True,
                changed_by=changed_by,
                change_note=payload.change_note,
            )
            row = repository.create(row)
            data = self._to_data(row)
            return GenericResponse.success_response(
                "Rules updated successfully.", data=data, status_code=HTTPStatus.OK
            )
        except ValidationException:
            raise
        except Exception:
            logger.exception("RuleService.update_rule_payload failed unexpectedly.")
            raise ServiceException() from None

    def list_versions(self, db: Session) -> GenericResponse[list[RuleConfigData]]:
        try:
            repository = RuleRepository(db)
            rows = repository.list_versions()
            if not rows:
                rows = [self.get_active_rule(db)]
            return GenericResponse.success_response(
                "Rule versions fetched.",
                data=[self._to_data(row) for row in rows],
            )
        except Exception:
            logger.exception("RuleService.list_versions failed unexpectedly.")
            raise ServiceException() from None

    def activate_version(
        self, db: Session, version: int, changed_by: str
    ) -> GenericResponse[RuleConfigData]:
        try:
            repository = RuleRepository(db)
            target = repository.get_by_version(version)
            if not target:
                raise NotFoundException("Rule version not found.")
            active = repository.get_active()
            if active and active.version != version:
                repository.deactivate(active)
            target.is_active = True
            target.changed_by = changed_by
            repository.commit()
            return GenericResponse.success_response("Rule version activated.", data=self._to_data(target))
        except NotFoundException:
            raise
        except Exception:
            logger.exception("RuleService.activate_version failed unexpectedly.")
            raise ServiceException() from None

    def preview_rule_payload(self, payload: RuleConfig) -> GenericResponse[RulePreviewData]:
        try:
            normalized = self._with_defaults(payload)
            self._validate(normalized)

            engine = EngineService()
            outcomes: list[dict[str, str | float]] = []
            for sample in self.SAMPLE_ANSWERS:
                answer_payload = [AnswerInput.model_validate(item) for item in sample["answers"]]
                computed = engine.compute(answer_payload, normalized)
                outcomes.append(
                    {
                        "scenario": str(sample["name"]),
                        "recommendation": computed.recommendation,
                        "agile_score": computed.agile_score,
                        "traditional_score": computed.traditional_score,
                        "confidence_level": self._confidence_level(
                            agile_score=computed.agile_score,
                            traditional_score=computed.traditional_score,
                        ),
                    }
                )

            data = RulePreviewData(
                normalized_payload=normalized,
                validation_passed=True,
                sample_outcomes=outcomes,
            )
            return GenericResponse.success_response("Rule preview generated.", data=data)
        except ValidationException:
            raise
        except Exception:
            logger.exception("RuleService.preview_rule_payload failed unexpectedly.")
            raise ServiceException() from None
