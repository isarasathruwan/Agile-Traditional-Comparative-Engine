from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.model.draft_model import EvidenceAnswerData
from app.model.traditional_advisor_model import TraditionalAdvisorData
from app.util.text_validation import validate_human_text

class ProfileInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    role: str = Field(min_length=2, max_length=100)
    company: str = Field(min_length=2, max_length=100)
    industry: str
    org_size: str
    project_name: str = Field(min_length=2, max_length=100)
    project_type: str
    duration: str
    team_size: str
    budget: str

    @field_validator("name", "role", "company", "project_name", mode="before")
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        v = v.strip()
        error = validate_human_text(v)
        if error:
            raise ValueError(error)
        return v


class AnswerInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_key: str
    construct_key: Literal["FLEXIBILITY", "PERFORMANCE", "STRICTNESS"] = Field(alias="construct")
    value: int = Field(ge=1, le=5)


class AssessmentCreateRequest(BaseModel):
    profile: ProfileInput
    answers: list[AnswerInput]
    profile_other_inputs: dict[str, str] | None = None
    draft_id: str | None = None
    session_id: str | None = None

    @field_validator("profile_other_inputs", mode="before")
    @classmethod
    def validate_profile_other_inputs(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("profile_other_inputs must be an object.")
        cleaned: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("profile_other_inputs keys must be strings.")
            if not isinstance(item, str):
                raise ValueError("profile_other_inputs values must be strings.")
            trimmed = item.strip()
            error = validate_human_text(trimmed)
            if error:
                raise ValueError(error)
            cleaned[key.strip()] = trimmed
        return cleaned or None


class AssessmentEventRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=100)
    event: Literal["opened", "question_answered"]
    question_key: str | None = None
    question_index: int | None = Field(default=None, ge=1, le=100)


class AssessmentEventData(BaseModel):
    session_id: str
    status: str
    answered_count: int


class AssessmentResultData(BaseModel):
    submission_id: int
    recommendation: Literal["Agile", "Traditional"]
    agile_score: float
    traditional_score: float
    construct_scores: dict[str, float]
    evidence_scoring: dict[str, object] = Field(default_factory=dict)
    dependent_variable_scores: dict[str, float]
    comparison_series: dict[str, list[float] | list[str]]
    insights: dict[str, str | float]
    decision_report: dict[str, object]
    ai_demo_trace: list[dict[str, object]]
    ai_demo_summary: dict[str, object]
    evidence_answers: list[EvidenceAnswerData] = Field(default_factory=list)
    traditional_advisor: TraditionalAdvisorData | None = None
    rationale: str
    rules_version: int
    questionnaire_version: int
    created_at: datetime
