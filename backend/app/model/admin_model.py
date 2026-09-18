from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.model.traditional_advisor_model import TraditionalAdvisorData


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserData(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: str


class AdminCurrentUserData(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    permissions: list[str]


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "analyst"

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def require_non_whitespace_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be blank.")
        return value


class AdminUserUpdateRequest(BaseModel):
    role: str
    is_active: bool


class RuleConfig(BaseModel):
    construct_weights: dict[str, float]
    agile_baseline: dict[str, float]
    traditional_baseline: dict[str, float]
    strictness_threshold: float = Field(ge=0, le=5)
    strictness_override_enabled: bool = True
    compatibility_normalization: Literal["legacy_fixed_15", "weighted_range"] = "legacy_fixed_15"
    dependent_variable_rules: dict[str, dict[str, float]] = Field(default_factory=dict)
    driver_rules: dict[str, dict[str, float | str]] = Field(default_factory=dict)
    risk_flag_rules: dict[str, dict[str, float | str]] = Field(default_factory=dict)
    explanation_templates: dict[str, str] = Field(default_factory=dict)
    next_step_templates: dict[str, list[str]] = Field(default_factory=dict)


class RuleConfigData(BaseModel):
    version: int
    payload: RuleConfig
    changed_by: str
    change_note: str
    created_at: str


class RuleConfigUpdateRequest(BaseModel):
    payload: RuleConfig
    change_note: str = ""


class RuleVersionActivateRequest(BaseModel):
    version: int


class RulePreviewRequest(BaseModel):
    payload: RuleConfig


class RulePreviewData(BaseModel):
    normalized_payload: RuleConfig
    validation_passed: bool
    sample_outcomes: list[dict[str, str | float]]


class AssessmentListItem(BaseModel):
    submission_id: int
    name: str
    company: str
    project_name: str
    recommendation: str
    agile_score: float
    traditional_score: float
    has_documents: bool
    questionnaire_version: int
    created_at: str


class CompanyGroupItem(BaseModel):
    company: str
    normalized_company: str
    submission_count: int
    latest_submission_at: str
    agile_count: int
    traditional_count: int
    avg_agile_score: float
    avg_traditional_score: float
    items: list[AssessmentListItem]


class AssessmentProfileAnswerData(BaseModel):
    question_id: str
    prompt: str
    profile_key: str
    answer: str
    selected_option: str | None = None
    other_text: str | None = None


class AssessmentLikertAnswerData(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    question_id: str
    prompt: str
    construct_key: str = Field(alias="construct")
    answer: int


class AssessmentDetailData(BaseModel):
    submission_id: int
    profile_answers: list[AssessmentProfileAnswerData]
    likert_answers: list[AssessmentLikertAnswerData]
    recommendation: str
    agile_score: float
    traditional_score: float
    construct_scores: dict[str, float]
    dependent_variable_scores: dict[str, float]
    insights: dict[str, str | float]
    decision_report: dict[str, object]
    ai_demo_trace: list[dict[str, object]]
    ai_demo_summary: dict[str, object]
    documents: list[dict[str, object]]
    traditional_advisor: TraditionalAdvisorData | None = None
    rules_version: int
    questionnaire_version: int
    created_at: str


class AssessmentDeleteData(BaseModel):
    submission_id: int
    deleted_documents: int
    deleted_session: bool
    deleted_draft: bool


class IncompleteActivityResetRequest(BaseModel):
    confirmation: str


class IncompleteActivityData(BaseModel):
    incomplete_sessions: int
    unsubmitted_drafts: int
    uploaded_documents: int
    processing_jobs: int
    evidence_records: int
    stored_file_count: int
    stored_file_bytes: int
    active_processing_jobs: int
    file_cleanup_failures: int = 0


class DocumentProcessingRetryData(BaseModel):
    submission_id: int
    queued_documents: int


class AnalyticsSummaryData(BaseModel):
    total_submissions: int
    agile_recommendations: int
    traditional_recommendations: int
    avg_agile_score: float
    avg_traditional_score: float


class ResearchMetricsData(BaseModel):
    questionnaire_version: int
    rules_version: int
    sample_size: int
    cronbach_alpha: dict[str, float | None]
    construct_score_means: dict[str, float]
    correlations: dict[str, float | None]
    t_tests: dict[str, dict[str, float | int | None]]
    dependent_variable_means: dict[str, dict[str, float]]
    confidence_distribution: dict[str, int]
    risk_flag_counts: dict[str, int]
    hybrid_readiness_distribution: dict[str, int]
    delivery_strategy_distribution: dict[str, int]
    strategy_option_counts: dict[str, int]
    evidence_adjusted: dict[str, object] = Field(default_factory=dict)


class TrendPoint(BaseModel):
    bucket: str
    total_submissions: int
    agile_recommendations: int
    traditional_recommendations: int
    avg_agile_score: float
    avg_traditional_score: float


class TrendsData(BaseModel):
    points: list[TrendPoint]


class DistributionsData(BaseModel):
    recommendation_distribution: dict[str, int]
    confidence_distribution: dict[str, int]
    risk_flag_distribution: dict[str, int]


class AiAnalyticsData(BaseModel):
    total_documented_assessments: int
    total_documents_processed: int
    duplicate_rejections: int
    average_trace_steps: float
    stage_frequency: dict[str, int]
    candidate_signal_frequency: dict[str, int]
    latest_activity: list[dict[str, object]]


class AssessmentWorkspaceAnalyticsData(BaseModel):
    opened_assessments: int
    answered_assessments: int
    fully_answered_assessments: int
    in_progress_assessments: int
    completed_submissions: int
    completion_rate: float
    draft_created_count: int
    uploaded_document_count: int
    document_backed_assessments: int
    total_documents_processed: int
    average_trace_steps: float
    stage_frequency: dict[str, int]
    candidate_signal_frequency: dict[str, int]
    processing_ready_count: int = 0
    processing_failed_count: int = 0
    evidence_suggested_count: int = 0
    evidence_confirmed_count: int = 0
    neutral_fallback_count: int = 0
