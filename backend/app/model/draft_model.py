from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DraftDocumentData(BaseModel):
    id: int
    filename: str
    content_type: str
    file_size: int
    status: str
    created_at: str


class DraftConsentRequest(BaseModel):
    consent_policy_version: str = "research-v1"
    google_ai_processing_accepted: bool
    research_document_attested: bool


class DraftProcessingData(BaseModel):
    status: str
    queued_jobs: int
    completed_jobs: int
    failed_jobs: int
    current_stage: str = "queued"
    current_stage_label: str = "Preparing secure processing"
    current_document_name: str | None = None
    processed_documents: int = 0
    total_documents: int = 0
    message: str | None = None


class EvidenceCitationData(BaseModel):
    document_id: int
    filename: str
    page_number: int
    excerpt: str


class EvidenceAnswerData(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    question_key: str
    prompt: str | None = None
    construct_key: str | None = Field(default=None, alias="construct")
    weight: float | None = None
    answer_type: str
    proposed_value: str | None
    confidence: str
    evidence_status: str
    final_value: str | None
    final_source: str | None
    citations: list[EvidenceCitationData]


class EvidenceAnswerUpdateRequest(BaseModel):
    action: Literal["confirm", "omit"]


class DocumentExtractedFactData(BaseModel):
    id: int
    document_id: int
    filename: str
    category: str
    label: str
    value: str
    confidence: str
    page_number: int
    excerpt: str


class DraftCreateResponse(BaseModel):
    draft_id: str
    status: str


class DraftStatusResponse(BaseModel):
    draft_id: str
    status: str
    duplicate_rejection_count: int
    uploads_locked: bool = False
    documents: list[DraftDocumentData]
    processing: DraftProcessingData
