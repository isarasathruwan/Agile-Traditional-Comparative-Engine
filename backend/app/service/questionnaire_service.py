import json
import logging
from http import HTTPStatus

from sqlalchemy.orm import Session

from app.entity.questionnaire_entity import QuestionnaireVersionEntity
from app.exceptions.domain_exception import NotFoundException, ServiceException, ValidationException
from app.model.questionnaire_model import (
    QuestionnaireData,
    QuestionnairePayload,
    QuestionnaireUpdateRequest,
)
from app.repository.questionnaire_repository import QuestionnaireRepository
from app.util.response import GenericResponse

logger = logging.getLogger(__name__)

DEFAULT_QUESTIONNAIRE = QuestionnairePayload(
    profile_questions=[
        {
            "question_id": "Q1",
            "kind": "text",
            "profile_key": "name",
            "prompt": "What's your name?",
            "placeholder": "Your full name",
        },
        {
            "question_id": "Q2",
            "kind": "pill",
            "profile_key": "role",
            "prompt": "What is your role?",
            "options": [
                "Project Manager",
                "Software Developer",
                "System Architect",
                "IS Practitioner",
                "Executive",
                "Other",
            ],
        },
        {
            "question_id": "Q3",
            "kind": "text",
            "profile_key": "company",
            "prompt": "What's your company name?",
            "placeholder": "Company or organization name",
        },
        {
            "question_id": "Q4",
            "kind": "pill",
            "profile_key": "industry",
            "prompt": "What industry are you in?",
            "options": [
                "Government",
                "Banking & Finance",
                "Healthcare",
                "Technology",
                "Telecom",
                "Education",
                "Retail",
                "Other",
            ],
        },
        {
            "question_id": "Q5",
            "kind": "pill",
            "profile_key": "orgSize",
            "prompt": "How large is your organization?",
            "options": ["1-10", "11-50", "51-200", "201-1,000", "1,000+"],
        },
        {
            "question_id": "Q6",
            "kind": "text",
            "profile_key": "projectName",
            "prompt": "What's the name of your project?",
            "placeholder": "Project name",
        },
        {
            "question_id": "Q7",
            "kind": "pill",
            "profile_key": "projectType",
            "prompt": "What type of project is this?",
            "options": ["New System", "System Integration", "Upgrade & Migration", "Maintenance", "Other"],
        },
        {
            "question_id": "Q8",
            "kind": "pill",
            "profile_key": "duration",
            "prompt": "What is the expected project duration?",
            "options": ["< 3 months", "3-6 months", "6-12 months", "1-2 years", "2+ years"],
        },
        {
            "question_id": "Q9",
            "kind": "pill",
            "profile_key": "teamSize",
            "prompt": "How large is your project team?",
            "options": ["1-5", "6-15", "16-30", "30+"],
        },
        {
            "question_id": "Q10",
            "kind": "pill",
            "profile_key": "budget",
            "prompt": "What is the approximate budget range?",
            "options": ["< $10K", "$10K-$50K", "$50K-$200K", "$200K-$1M", "$1M+", "Prefer not to say"],
        },
    ],
    likert_questions=[
        {
            "question_id": "Q11",
            "construct": "FLEXIBILITY",
            "prompt": "How much are requirements expected to change after development begins?",
            "scale_labels": ["Stable", "Minor change", "Occasional change", "Frequent change", "Constant or substantial change"],
        },
        {
            "question_id": "Q12",
            "construct": "FLEXIBILITY",
            "prompt": "How much uncertainty exists about the final solution and its acceptance criteria?",
            "scale_labels": ["Fully defined", "Mostly defined", "Partly defined", "Significant uncertainty", "Substantial discovery required"],
        },
        {
            "question_id": "Q13",
            "construct": "FLEXIBILITY",
            "prompt": "How often can an authorized stakeholder review work and make priority decisions?",
            "scale_labels": ["Major milestones only", "Monthly", "Every 2–4 weeks", "Weekly", "Whenever needed"],
        },
        {
            "question_id": "Q14",
            "construct": "FLEXIBILITY",
            "prompt": "How capable is the team of planning, building, testing, and reviewing work in short cycles?",
            "scale_labels": ["No capability", "Limited", "Developing", "Capable", "Highly experienced"],
        },
        {
            "question_id": "Q15",
            "construct": "PERFORMANCE",
            "prompt": "How fixed is the delivery date because of contractual, legal, launch, or external commitments?",
            "scale_labels": ["Flexible", "Target only", "Important with flexibility", "Externally committed", "Immovable"],
        },
        {
            "question_id": "Q16",
            "construct": "PERFORMANCE",
            "prompt": "How fixed is the project budget or funding ceiling?",
            "scale_labels": ["Flexible", "Broad tolerance", "Moderate constraint", "Tight constraint", "No overrun permitted"],
        },
        {
            "question_id": "Q17",
            "construct": "PERFORMANCE",
            "prompt": "How much formal approval is required before the delivery plan can be changed?",
            "scale_labels": ["Team discretion", "Lightweight approval", "Manager approval", "Multiple approvals", "Contractual or board approval"],
        },
        {
            "question_id": "Q18",
            "construct": "STRICTNESS",
            "prompt": "What level of regulatory, legal, or audit obligation applies?",
            "scale_labels": ["None", "Low", "Moderate", "High", "Extensive mandatory obligations"],
        },
        {
            "question_id": "Q19",
            "construct": "STRICTNESS",
            "prompt": "What is the highest credible consequence if the system fails or is compromised?",
            "scale_labels": ["Low and reversible", "Limited", "Moderate", "Serious", "Severe or legally significant"],
        },
        {
            "question_id": "Q20",
            "construct": "STRICTNESS",
            "prompt": "How much controlled documentation and end-to-end traceability is required?",
            "scale_labels": ["Working notes", "Basic", "Standard", "Detailed", "Complete audit-grade traceability"],
        },
        {
            "question_id": "Q21",
            "construct": "STRICTNESS",
            "prompt": "How dependent is delivery on external vendors, legacy systems, or interfaces outside the team's control?",
            "scale_labels": ["Self-contained", "Few dependencies", "Moderate", "Several critical dependencies", "Many critical external dependencies"],
        },
        {
            "question_id": "Q22",
            "construct": "STRICTNESS",
            "prompt": "How much coordination and sequencing is required across teams or organizations?",
            "scale_labels": ["One small team", "Few interactions", "Multiple teams", "Distributed sequencing", "Tightly coupled multi-organization delivery"],
        },
    ],
    document_questions=[
        {
            "question_id": "D01",
            "construct": "FLEXIBILITY",
            "prompt": "The document shows that requirements are expected to materially change after delivery begins.",
        },
        {
            "question_id": "D02",
            "construct": "FLEXIBILITY",
            "prompt": "The document requires discovery, prototyping, piloting, or phased validation before the scope is settled.",
        },
        {
            "question_id": "D03",
            "construct": "FLEXIBILITY",
            "prompt": "The document commits named business stakeholders to recurring reviews, demonstrations, or feedback.",
        },
        {
            "question_id": "D04",
            "construct": "PERFORMANCE",
            "prompt": "The document establishes a fixed or externally committed delivery date.",
        },
        {
            "question_id": "D05",
            "construct": "PERFORMANCE",
            "prompt": "The document establishes a fixed budget, funding ceiling, or explicit cost-overrun constraint.",
        },
        {
            "question_id": "D06",
            "construct": "PERFORMANCE",
            "prompt": "The document requires fixed milestones, predefined deliverables, or formal acceptance before release.",
        },
        {
            "question_id": "D07",
            "construct": "STRICTNESS",
            "prompt": "The document identifies mandatory regulatory, legal, audit, or records-retention obligations.",
        },
        {
            "question_id": "D08",
            "construct": "STRICTNESS",
            "prompt": "The document requires formal security, privacy, safety, or assurance controls.",
        },
        {
            "question_id": "D09",
            "construct": "STRICTNESS",
            "prompt": "The document shows delivery depends on external vendors, legacy platforms, or multiple system interfaces.",
        },
        {
            "question_id": "D10",
            "construct": "STRICTNESS",
            "prompt": "The document requires formal change, procurement, architecture, or release approval gates.",
        },
    ],
)


class QuestionnaireService:
    @staticmethod
    def _validate_payload(payload: QuestionnairePayload) -> None:
        profile_keys = {
            "name",
            "role",
            "company",
            "industry",
            "orgSize",
            "projectName",
            "projectType",
            "duration",
            "teamSize",
            "budget",
        }
        profile_ids = [item.question_id for item in payload.profile_questions]
        likert_ids = [item.question_id for item in payload.likert_questions]
        document_ids = [item.question_id for item in payload.document_questions]
        all_ids = profile_ids + likert_ids + document_ids
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("Question IDs must be unique across questionnaire.")
        if not payload.profile_questions or not payload.likert_questions:
            raise ValueError("Both profile and likert sections are required.")

        for item in payload.profile_questions:
            if item.profile_key not in profile_keys:
                raise ValueError(f"Invalid profile key: {item.profile_key}")
            if item.kind == "pill" and (not item.options or len(item.options) < 2):
                raise ValueError(f"Pill question requires at least two options: {item.question_id}")
            if item.kind == "text" and item.options:
                raise ValueError(f"Text question cannot include options: {item.question_id}")
            if item.document_extraction.answer_type == "option" and not item.options:
                raise ValueError(f"Option extraction requires options: {item.question_id}")
            if item.document_extraction.enabled:
                raise ValueError("Document extraction is only supported by document-only evidence questions.")

        for item in payload.likert_questions:
            if item.document_extraction.enabled and item.document_extraction.answer_type != "likert":
                raise ValueError(f"Likert extraction must use answer_type=likert: {item.question_id}")
            if item.document_extraction.enabled:
                raise ValueError("Document extraction is only supported by document-only evidence questions.")

        for item in payload.document_questions:
            if not item.document_extraction.enabled or item.document_extraction.answer_type != "likert":
                raise ValueError(f"Document question extraction must be enabled and use answer_type=likert: {item.question_id}")

        constructs = {item.construct_key for item in payload.likert_questions}
        required_constructs = {"FLEXIBILITY", "PERFORMANCE", "STRICTNESS"}
        if not required_constructs.issubset(constructs):
            raise ValueError("Likert questions must include FLEXIBILITY, PERFORMANCE, and STRICTNESS constructs.")

    def _serialize(self, row: QuestionnaireVersionEntity) -> QuestionnaireData:
        payload = QuestionnairePayload(**json.loads(row.payload_json))
        return QuestionnaireData(
            version=row.version,
            title=row.title,
            payload=payload,
            changed_by=row.changed_by,
            change_note=row.change_note,
            created_at=row.created_at.isoformat(),
        )

    def get_active(self, db: Session) -> QuestionnaireVersionEntity:
        repository = QuestionnaireRepository(db)
        active = repository.get_active()
        if active:
            return active
        seed = QuestionnaireVersionEntity(
            version=1,
            title="Default Questionnaire",
            payload_json=DEFAULT_QUESTIONNAIRE.model_dump_json(),
            is_active=True,
            changed_by="system",
            change_note="Initial seed",
        )
        return repository.create(seed)

    def get_active_payload(self, db: Session) -> GenericResponse[QuestionnaireData]:
        try:
            return GenericResponse.success_response(
                message="Active questionnaire fetched.",
                data=self._serialize(self.get_active(db)),
            )
        except Exception:
            logger.exception("QuestionnaireService.get_active_payload failed unexpectedly.")
            raise ServiceException() from None

    def list_versions(self, db: Session) -> GenericResponse[list[QuestionnaireData]]:
        try:
            repository = QuestionnaireRepository(db)
            rows = repository.list_versions()
            if not rows:
                rows = [self.get_active(db)]
            return GenericResponse.success_response(
                message="Questionnaire versions fetched.",
                data=[self._serialize(row) for row in rows],
            )
        except Exception:
            logger.exception("QuestionnaireService.list_versions failed unexpectedly.")
            raise ServiceException() from None

    def create_version(
        self, db: Session, payload: QuestionnaireUpdateRequest, changed_by: str
    ) -> GenericResponse[QuestionnaireData]:
        try:
            self._validate_payload(payload.payload)
            repository = QuestionnaireRepository(db)
            active = self.get_active(db)
            repository.deactivate(active)
            version = repository.get_latest_version() + 1
            row = QuestionnaireVersionEntity(
                version=version,
                title=payload.title,
                payload_json=payload.payload.model_dump_json(),
                is_active=True,
                changed_by=changed_by,
                change_note=payload.change_note,
            )
            row = repository.create(row)
            return GenericResponse.success_response(
                message="Questionnaire updated successfully.",
                data=self._serialize(row),
                status_code=HTTPStatus.OK,
            )
        except ValueError as exc:
            raise ValidationException(str(exc)) from None
        except Exception:
            logger.exception("QuestionnaireService.create_version failed unexpectedly.")
            raise ServiceException() from None

    def activate_version(
        self, db: Session, version: int, changed_by: str
    ) -> GenericResponse[QuestionnaireData]:
        try:
            repository = QuestionnaireRepository(db)
            target = repository.get_by_version(version)
            if not target:
                raise NotFoundException("Questionnaire version not found.")
            active = repository.get_active()
            if active and active.version != target.version:
                repository.deactivate(active)
            target.is_active = True
            target.changed_by = changed_by
            repository.commit()
            return GenericResponse.success_response(
                message="Questionnaire version activated.",
                data=self._serialize(target),
            )
        except NotFoundException:
            raise
        except Exception:
            logger.exception("QuestionnaireService.activate_version failed unexpectedly.")
            raise ServiceException() from None
