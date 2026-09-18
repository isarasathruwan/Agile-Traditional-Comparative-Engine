export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface AssessmentAnswerPayload {
  question_key: string;
  construct: "FLEXIBILITY" | "PERFORMANCE" | "STRICTNESS";
  value: number;
}

export interface ProfileQuestion {
  question_id: string;
  kind: "text" | "pill";
  profile_key: string;
  prompt: string;
  placeholder?: string | null;
  options?: string[] | null;
  document_extraction?: {
    enabled: boolean;
    instruction: string;
    answer_type: "text" | "option" | "likert";
    rubric?: string | null;
  };
}

export interface LikertQuestion {
  question_id: string;
  construct: "FLEXIBILITY" | "PERFORMANCE" | "STRICTNESS";
  prompt: string;
  scale_labels: [string, string, string, string, string];
  document_extraction?: {
    enabled: boolean;
    instruction: string;
    answer_type: "text" | "option" | "likert";
    rubric?: string | null;
  };
}

export interface DocumentQuestion {
  question_id: string;
  construct: "FLEXIBILITY" | "PERFORMANCE" | "STRICTNESS";
  prompt: string;
  weight: number;
}

export interface QuestionnairePayload {
  profile_questions: ProfileQuestion[];
  likert_questions: LikertQuestion[];
  document_questions: DocumentQuestion[];
}

export interface QuestionnaireResponse {
  version: number;
  title: string;
  payload: QuestionnairePayload;
  changed_by: string;
  change_note: string;
  created_at: string;
}

export const DEFAULT_LIKERT_SCALE_LABELS: LikertQuestion["scale_labels"] = [
  "Strongly disagree",
  "Disagree",
  "Neutral",
  "Agree",
  "Strongly agree",
];

export interface AssessmentCreatePayload {
  profile: {
    name: string;
    role: string;
    company: string;
    industry: string;
    org_size: string;
    project_name: string;
    project_type: string;
    duration: string;
    team_size: string;
    budget: string;
  };
  answers: AssessmentAnswerPayload[];
  profile_other_inputs?: Record<string, string> | null;
  draft_id?: string | null;
  session_id?: string | null;
}

export interface AssessmentEventPayload {
  session_id: string;
  event: "opened" | "question_answered";
  question_key?: string;
  question_index?: number;
}

export interface AssessmentCreateResponse {
  submission_id: number;
  recommendation: "Agile" | "Traditional";
  agile_score: number;
  traditional_score: number;
  construct_scores: Record<string, number>;
  evidence_scoring: {
    questionnaire_construct_scores: Record<string, number>;
    document_construct_scores: Record<string, number | null>;
    document_coverage: Record<string, number>;
    document_contribution: Record<string, number>;
    decision_construct_scores: Record<string, number>;
    document_evidence_cap: number;
    confirmed_item_count: number;
  };
  dependent_variable_scores: Record<string, number>;
  comparison_series: {
    dimensions: string[];
    project: number[];
    agile: number[];
    traditional: number[];
  };
  insights: {
    recommended_direction: string;
    strongest_dimension: string;
    strongest_score: number;
    weakest_dimension: string;
    weakest_score: number;
    score_gap: number;
    confidence_level: "high" | "moderate" | "close";
  };
  decision_report: {
    recommendation: "Agile" | "Traditional";
    confidence_level: "high" | "moderate" | "close";
    score_gap: number;
    methodology_fit_summary: string;
    outcome_scores: Record<string, number>;
    drivers: Array<{
      key: string;
      label: string;
      methodology: string;
      construct: string;
      score: number;
    }>;
    risk_flags: Array<{
      key: string;
      label: string;
      metric: string;
      value: number;
    }>;
    tradeoffs: {
      strengths: string[];
      watch_areas: string[];
      methodology_note: string[];
    };
    hypothesis_evidence: Record<string, { label: string; score: number }>;
    strategy_profile: {
      hybrid_readiness: {
        score: number;
        level: "low" | "moderate" | "high";
        rationale: string[];
      };
      delivery_strategy: string;
      strategy_options: Array<{
        key: string;
        label: string;
        fit: string;
        reason: string;
      }>;
      governance_controls: string[];
      research_boundary_note: string;
    };
    next_steps: string[];
    limitations: string[];
  };
  ai_demo_trace: Array<{
    stage: string;
    label: string;
    status: string;
    detail: string;
    artifacts: unknown;
    duration_ms: number;
  }>;
  ai_demo_summary: {
    documents_processed: number;
    trace_steps: number;
    candidate_signals: Array<{
      key: string;
      label: string;
      value: string | number;
      confidence: string;
      source: string;
    }>;
    document_filenames: string[];
    demo_mode: boolean;
    explanation_scope: string;
  };
  evidence_answers: EvidenceAnswerData[];
  traditional_advisor?: TraditionalAdvisorData | null;
  rationale: string;
  rules_version: number;
  questionnaire_version: number;
  created_at: string;
}

export interface TraditionalAdvisorCitation {
  document_id: number;
  filename: string;
  page_number: number | null;
  claim: string;
  excerpt: string;
}

export interface TraditionalAdvisorData {
  submission_id: number;
  status: "not_applicable" | "queued" | "running" | "ready" | "failed";
  retry_allowed: boolean;
  generated_at: string | null;
  error_message: string | null;
  advisor: {
    recommended_method: string;
    recommendation_summary: string;
    rationale: string;
    alternatives: Array<{ method: string; reason: string }>;
    rollout: Array<{ phase: string; objective: string; actions: string[]; control_artifacts: string[] }>;
    tradeoffs: string[];
    evidence: Array<{ claim: string; citations: TraditionalAdvisorCitation[] }>;
    limitations: string[];
  } | null;
}

export async function getTraditionalAdvisor(submissionId: number): Promise<TraditionalAdvisorData> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessments/${submissionId}/traditional-advisor`, {
    credentials: "include",
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Unable to load delivery advice");
  return envelope.data as TraditionalAdvisorData;
}

export async function retryTraditionalAdvisor(submissionId: number): Promise<TraditionalAdvisorData> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessments/${submissionId}/traditional-advisor/retry`, {
    method: "POST",
    credentials: "include",
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Unable to retry delivery advice");
  return envelope.data as TraditionalAdvisorData;
}

export async function createAssessment(
  payload: AssessmentCreatePayload
): Promise<AssessmentCreateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessments`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to submit assessment");
  }
  const envelope = (await response.json()) as {
    success: boolean;
    message: string;
    data: AssessmentCreateResponse | null;
  };
  if (!envelope.success || !envelope.data) {
    throw new Error(envelope.message || "Failed to submit assessment");
  }
  return envelope.data;
}

export async function trackAssessmentEvent(payload: AssessmentEventPayload): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessments/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) {
    throw new Error(envelope.message || "Failed to track assessment event");
  }
}

export async function getActiveQuestionnaire(): Promise<QuestionnaireResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/questionnaire/active`);
  if (!response.ok) {
    throw new Error("Failed to fetch questionnaire");
  }
  const envelope = (await response.json()) as {
    success: boolean;
    message: string;
    data: QuestionnaireResponse | null;
  };
  if (!envelope.success || !envelope.data) {
    throw new Error(envelope.message || "Failed to fetch questionnaire");
  }
  return envelope.data;
}

export interface DraftDocumentData {
  id: number;
  filename: string;
  content_type: string;
  file_size: number;
  status: string;
  created_at: string;
}

export interface DraftCreateResponse {
  draft_id: string;
  status: string;
}

export interface DraftStatusResponse {
  draft_id: string;
  status: string;
  duplicate_rejection_count: number;
  uploads_locked: boolean;
  documents: DraftDocumentData[];
  processing: {
    status: string;
    queued_jobs: number;
    completed_jobs: number;
    failed_jobs: number;
    current_stage: "queued" | "extracting" | "embedding" | "reasoning" | "ready" | "failed";
    current_stage_label: string;
    current_document_name?: string | null;
    processed_documents: number;
    total_documents: number;
    message?: string | null;
  };
}

export interface EvidenceAnswerData {
  question_key: string;
  prompt: string | null;
  construct: "FLEXIBILITY" | "PERFORMANCE" | "STRICTNESS" | null;
  weight: number | null;
  answer_type: "text" | "option" | "likert";
  proposed_value: string | null;
  confidence: string;
  evidence_status: string;
  final_value: string | null;
  final_source: string | null;
  citations: Array<{
    document_id: number;
    filename: string;
    page_number: number;
    excerpt: string;
  }>;
}

export interface DocumentExtractedFactData {
  id: number;
  document_id: number;
  filename: string;
  category: string;
  label: string;
  value: string;
  confidence: string;
  page_number: number;
  excerpt: string;
}

export async function createDraft(assessmentSessionId?: string | null): Promise<DraftCreateResponse> {
  const search = assessmentSessionId
    ? `?assessment_session_id=${encodeURIComponent(assessmentSessionId)}`
    : "";
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts${search}`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) throw new Error("Failed to create draft");
  const envelope = await response.json();
  if (!envelope.success) throw new Error(envelope.message);
  return envelope.data as DraftCreateResponse;
}

export async function recordDraftConsent(draftId: string): Promise<DraftStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/consent`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      consent_policy_version: "research-v1",
      google_ai_processing_accepted: true,
      research_document_attested: true,
    }),
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Unable to record document consent");
  return envelope.data as DraftStatusResponse;
}

export async function uploadDocument(draftId: string, file: File): Promise<DraftDocumentData> {
  const formData = new FormData();
  formData.append("file", file);
  
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/documents`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Failed to upload document");
  return envelope.data as DraftDocumentData;
}

export async function deleteDraftDocument(draftId: string, documentId: number): Promise<DraftStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/documents/${documentId}`, {
    method: "DELETE",
    credentials: "include",
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Unable to remove document");
  return envelope.data as DraftStatusResponse;
}

export async function startDocumentProcessing(draftId: string): Promise<DraftStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/process`, {
    method: "POST",
    credentials: "include",
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Unable to start document analysis");
  return envelope.data as DraftStatusResponse;
}

export async function getDraftStatus(draftId: string): Promise<DraftStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/documents/status`, {
    credentials: "include",
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Failed to get draft status");
  return envelope.data as DraftStatusResponse;
}

export async function getEvidenceAnswers(draftId: string): Promise<EvidenceAnswerData[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/evidence-answers`, {
    credentials: "include",
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Unable to load evidence answers");
  return envelope.data as EvidenceAnswerData[];
}

export async function getDocumentExtractions(draftId: string): Promise<DocumentExtractedFactData[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/document-extractions`, {
    credentials: "include",
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Unable to load extracted document facts");
  return envelope.data as DocumentExtractedFactData[];
}

export async function getDocumentPreview(draftId: string, documentId: number): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/documents/${documentId}/preview`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Unable to prepare the document preview");
  }
  return response.blob();
}

export async function confirmEvidenceAnswer(
  draftId: string,
  questionKey: string,
  action: "confirm" | "omit"
): Promise<EvidenceAnswerData> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessment-drafts/${draftId}/evidence-answers/${questionKey}`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.message || "Unable to confirm evidence answer");
  return envelope.data as EvidenceAnswerData;
}
