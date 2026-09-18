export type AssessmentDetail = {
  submission_id: number;
  profile_answers: Array<{
    question_id: string;
    prompt: string;
    profile_key: string;
    answer: string;
    selected_option?: string | null;
    other_text?: string | null;
  }>;
  likert_answers: Array<{
    question_id: string;
    prompt: string;
    construct: string;
    answer: number;
  }>;
  recommendation: string;
  agile_score: number;
  traditional_score: number;
  construct_scores: Record<string, number>;
  dependent_variable_scores: Record<string, number>;
  insights: Record<string, string | number>;
  decision_report: Record<string, unknown>;
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
  documents: Array<{
    id: number;
    filename: string;
    content_type: string;
    file_size: number;
    status: string;
    created_at: string;
    preview_url: string;
    download_url: string;
  }>;
  traditional_advisor?: {
    status: "not_applicable" | "queued" | "running" | "ready" | "failed";
    retry_allowed: boolean;
    error_message: string | null;
    advisor: {
      recommended_method: string;
      recommendation_summary: string;
      rationale: string;
      alternatives: Array<{ method: string; reason: string }>;
      rollout: Array<{ phase: string; objective: string; actions: string[]; control_artifacts: string[] }>;
      tradeoffs: string[];
      evidence: Array<{ claim: string; citations: Array<{ filename: string; page_number: number | null }> }>;
      limitations: string[];
    } | null;
  } | null;
  rules_version: number;
  questionnaire_version: number;
  created_at: string;
};
