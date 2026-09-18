from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


DEFAULT_LIKERT_SCALE_LABELS = [
    "Strongly disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
]


class DocumentExtractionConfig(BaseModel):
    enabled: bool = False
    instruction: str = "Extract a direct answer only when the document contains supporting evidence."
    answer_type: Literal["text", "option", "likert"] = "text"
    rubric: str | None = None


class ProfileQuestion(BaseModel):
    question_id: str
    kind: Literal["text", "pill"]
    profile_key: str
    prompt: str
    placeholder: str | None = None
    options: list[str] | None = None
    document_extraction: DocumentExtractionConfig = Field(default_factory=DocumentExtractionConfig)


class LikertQuestion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    question_id: str
    construct_key: Literal["FLEXIBILITY", "PERFORMANCE", "STRICTNESS"] = Field(alias="construct")
    prompt: str
    scale_labels: list[str] = Field(
        default_factory=lambda: list(DEFAULT_LIKERT_SCALE_LABELS),
        min_length=5,
        max_length=5,
    )
    document_extraction: DocumentExtractionConfig = Field(
        default_factory=lambda: DocumentExtractionConfig(
            enabled=False,
            answer_type="likert",
            instruction="Use only direct document evidence. Return a score from 1 to 5 and cite the supporting text.",
            rubric="This user-reported question is not extracted from documents.",
        )
    )

    @field_validator("scale_labels")
    @classmethod
    def validate_scale_labels(cls, value: list[str]) -> list[str]:
        cleaned = [label.strip() for label in value]
        if any(not label for label in cleaned):
            raise ValueError("All five Likert scale labels are required.")
        if cleaned[0] == cleaned[-1]:
            raise ValueError("Likert scale endpoint labels must be different.")
        return cleaned


class DocumentQuestion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    question_id: str
    construct_key: Literal["FLEXIBILITY", "PERFORMANCE", "STRICTNESS"] = Field(alias="construct")
    prompt: str
    weight: float = Field(default=1.0, gt=0, le=3)
    document_extraction: DocumentExtractionConfig = Field(
        default_factory=lambda: DocumentExtractionConfig(
            enabled=True,
            answer_type="likert",
            instruction="Use only direct, cited document evidence. Do not infer missing facts.",
            rubric=(
                "Score 1 for explicit low or absent evidence, 3 for explicit bounded or mixed evidence, "
                "and 5 for explicit high, fixed, or mandatory evidence. Return no answer when unsupported."
            ),
        )
    )


class QuestionnairePayload(BaseModel):
    profile_questions: list[ProfileQuestion]
    likert_questions: list[LikertQuestion]
    document_questions: list[DocumentQuestion] = Field(default_factory=list)


class QuestionnaireData(BaseModel):
    version: int
    title: str
    payload: QuestionnairePayload
    changed_by: str
    change_note: str
    created_at: str


class QuestionnaireUpdateRequest(BaseModel):
    title: str = "Questionnaire"
    payload: QuestionnairePayload
    change_note: str = ""
