from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TraditionalAdvisorStatus = Literal["not_applicable", "queued", "running", "ready", "failed"]


class TraditionalAdvisorCitation(BaseModel):
    document_id: int
    filename: str
    page_number: int | None = None
    claim: str
    excerpt: str


class TraditionalAdvisorEvidence(BaseModel):
    claim: str
    citations: list[TraditionalAdvisorCitation] = Field(default_factory=list)


class TraditionalAdvisorAlternative(BaseModel):
    method: str
    reason: str


class TraditionalAdvisorRolloutPhase(BaseModel):
    phase: str
    objective: str
    actions: list[str] = Field(min_length=1)
    control_artifacts: list[str] = Field(default_factory=list)


class TraditionalAdvisorPayload(BaseModel):
    recommended_method: str
    recommendation_summary: str
    rationale: str
    alternatives: list[TraditionalAdvisorAlternative] = Field(min_length=2, max_length=2)
    rollout: list[TraditionalAdvisorRolloutPhase] = Field(min_length=3, max_length=3)
    tradeoffs: list[str] = Field(default_factory=list)
    evidence: list[TraditionalAdvisorEvidence] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class TraditionalAdvisorData(BaseModel):
    submission_id: int
    status: TraditionalAdvisorStatus
    retry_allowed: bool = False
    generated_at: datetime | None = None
    error_message: str | None = None
    advisor: TraditionalAdvisorPayload | None = None
