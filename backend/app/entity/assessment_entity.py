from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database_config import Base
from app.entity.base_mixin import TimestampMixin
from app.entity.draft_entity import AssessmentDraftEntity  # noqa: F401


class AssessmentSubmissionEntity(Base, TimestampMixin):
    __tablename__ = "assessment_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    normalized_company: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    profile_other_inputs: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("assessment_drafts.id"), nullable=True)
    industry: Mapped[str] = mapped_column(String(255))
    org_size: Mapped[str] = mapped_column(String(255))
    project_name: Mapped[str] = mapped_column(String(255))
    project_type: Mapped[str] = mapped_column(String(255))
    duration: Mapped[str] = mapped_column(String(255))
    team_size: Mapped[str] = mapped_column(String(255))
    budget: Mapped[str] = mapped_column(String(255))


class AssessmentAnswerEntity(Base):
    __tablename__ = "assessment_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("assessment_submissions.id"))
    question_key: Mapped[str] = mapped_column(String(100))
    construct: Mapped[str] = mapped_column(String(50))
    value: Mapped[int] = mapped_column(Integer)


class AssessmentResultEntity(Base, TimestampMixin):
    __tablename__ = "assessment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("assessment_submissions.id"), unique=True)
    recommendation: Mapped[str] = mapped_column(String(30))
    agile_score: Mapped[float] = mapped_column(Float)
    traditional_score: Mapped[float] = mapped_column(Float)
    flexibility_score: Mapped[float] = mapped_column(Float)
    performance_score: Mapped[float] = mapped_column(Float)
    strictness_score: Mapped[float] = mapped_column(Float)
    rationale: Mapped[str] = mapped_column(Text)
    dependent_variable_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    comparison_series: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    decision_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_demo_trace: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ai_demo_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rules_version: Mapped[int] = mapped_column(Integer)
    questionnaire_version: Mapped[int] = mapped_column(Integer, default=1)


class AssessmentSessionEntity(Base, TimestampMixin):
    __tablename__ = "assessment_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="opened")
    answered_count: Mapped[int] = mapped_column(Integer, default=0)
    last_question_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    opened_at: Mapped[DateTime] = mapped_column(DateTime)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    draft_created_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    submission_id: Mapped[int | None] = mapped_column(ForeignKey("assessment_submissions.id"), nullable=True)
