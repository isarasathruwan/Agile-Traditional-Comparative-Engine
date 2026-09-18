"use client";

import { FormEvent, Fragment, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { Trash } from "@phosphor-icons/react";
import { API_BASE_URL, DEFAULT_LIKERT_SCALE_LABELS } from "@/lib/api";
import { adminDelete, adminGet, adminGetEnvelope, adminLogin, adminPost, adminPut, isAdminUnauthenticated } from "@/lib/adminApi";
import { ADMIN_SECTION_LABELS, PRODUCT_NAME, adminPageTitle, type AdminSectionKey } from "@/lib/pageMeta";
import AdminWorkspaceShell from "@/components/admin/AdminWorkspaceShell";

type Summary = {
  total_submissions: number;
  agile_recommendations: number;
  traditional_recommendations: number;
  avg_agile_score: number;
  avg_traditional_score: number;
};

type ResearchMetrics = {
  questionnaire_version: number;
  rules_version: number;
  sample_size: number;
  cronbach_alpha: Record<string, number | null>;
  construct_score_means: Record<string, number>;
  correlations: Record<string, number | null>;
  t_tests: Record<string, Record<string, number | null>>;
  dependent_variable_means: Record<string, Record<string, number>>;
  confidence_distribution: Record<string, number>;
  risk_flag_counts: Record<string, number>;
  hybrid_readiness_distribution: Record<string, number>;
  delivery_strategy_distribution: Record<string, number>;
  strategy_option_counts: Record<string, number>;
  evidence_adjusted: {
    documented_assessments: number;
    assessments_with_score_adjustment: number;
    average_coverage: Record<string, number>;
    maximum_construct_contribution: number;
  };
};

type AssessmentWorkspaceAnalytics = {
  opened_assessments: number;
  answered_assessments: number;
  fully_answered_assessments: number;
  in_progress_assessments: number;
  completed_submissions: number;
  completion_rate: number;
  draft_created_count: number;
  uploaded_document_count: number;
  document_backed_assessments: number;
  total_documents_processed: number;
  average_trace_steps: number;
  stage_frequency: Record<string, number>;
  candidate_signal_frequency: Record<string, number>;
  processing_ready_count: number;
  processing_failed_count: number;
  evidence_suggested_count: number;
  evidence_confirmed_count: number;
  neutral_fallback_count: number;
};

type IncompleteActivityData = {
  incomplete_sessions: number;
  unsubmitted_drafts: number;
  uploaded_documents: number;
  processing_jobs: number;
  evidence_records: number;
  stored_file_count: number;
  stored_file_bytes: number;
  active_processing_jobs: number;
  file_cleanup_failures: number;
};

type AdminUser = {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

type AdminIdentity = {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  permissions: string[];
};

type ProfileQuestion = {
  question_id: string;
  kind: "text" | "pill";
  profile_key: string;
  prompt: string;
  placeholder?: string | null;
  options?: string[] | null;
  document_extraction?: DocumentExtractionConfig;
};

type DocumentExtractionConfig = {
  enabled: boolean;
  instruction: string;
  answer_type: "text" | "option" | "likert";
  rubric?: string | null;
};

type LikertQuestion = {
  question_id: string;
  construct: "FLEXIBILITY" | "PERFORMANCE" | "STRICTNESS";
  prompt: string;
  scale_labels: [string, string, string, string, string];
  document_extraction?: DocumentExtractionConfig;
};

type DocumentQuestion = {
  question_id: string;
  construct: "FLEXIBILITY" | "PERFORMANCE" | "STRICTNESS";
  prompt: string;
  weight: number;
  document_extraction?: DocumentExtractionConfig;
};

type QuestionnairePayload = {
  profile_questions: ProfileQuestion[];
  likert_questions: LikertQuestion[];
  document_questions: DocumentQuestion[];
};

type RulePreview = {
  normalized_payload: Record<string, unknown>;
  validation_passed: boolean;
  sample_outcomes: Array<Record<string, string | number>>;
};

type AssessmentListItem = {
  submission_id: number;
  name: string;
  company: string;
  project_name: string;
  recommendation: string;
  agile_score: number;
  traditional_score: number;
  has_documents: boolean;
  questionnaire_version: number;
  created_at: string;
};

type CompanyGroupItem = {
  company: string;
  normalized_company: string;
  submission_count: number;
  latest_submission_at: string;
  agile_count: number;
  traditional_count: number;
  avg_agile_score: number;
  avg_traditional_score: number;
  items: AssessmentListItem[];
};

type PaginatedEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
};

type SectionKey = AdminSectionKey;

const SECTION_TIPS: Record<SectionKey, { title: string; body: string; note: string }> = {
  overview: {
    title: "Quick snapshot",
    body: "Use this page to quickly understand how many assessments were completed and the overall recommendation trend.",
    note: "If these numbers look unusual, review recent assessments first.",
  },
  assessments: {
    title: "Find and review submissions",
    body: "Review completed assessments, document-backed runs, funnel metrics, and AI trace details in one workspace.",
    note: "Use CSV download for sharing data outside the dashboard.",
  },
  rules: {
    title: "Decision settings",
    body: "These settings control how recommendations are calculated.",
    note: "Changes affect future assessments. Use Preview before saving.",
  },
  questionnaire: {
    title: "Question setup",
    body: "Edit the question text and order shown to clients during the assessment.",
    note: "Save as a new version so you can safely activate changes later.",
  },
  users: {
    title: "Team access",
    body: "Manage who can log in and what responsibilities they have.",
    note: "Only grant high-access roles to trusted admins.",
  },
};

const SHELL_BACKGROUND =
  "bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.16),transparent_28%),radial-gradient(circle_at_top_right,_rgba(13,148,136,0.14),transparent_22%),linear-gradient(180deg,#f7fbfa_0%,#ffffff_36%,#f8fafc_100%)]";
const PANEL_CLASS =
  "rounded-[28px] border border-emerald-100/80 bg-white/90 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.28)] backdrop-blur-sm";
const SOFT_PANEL_CLASS =
  "rounded-[24px] border border-emerald-100/80 bg-gradient-to-br from-white via-emerald-50/40 to-teal-50/60";
const INPUT_CLASS =
  "w-full rounded-2xl border border-emerald-100 bg-white px-3 py-2 text-base text-slate-800 shadow-[inset_0_1px_0_rgba(255,255,255,0.9)] outline-none transition focus:border-emerald-300 focus:ring-4 focus:ring-emerald-100";
const PRIMARY_BUTTON_CLASS =
  "rounded-full border border-emerald-700 bg-emerald-700 px-5 py-2 text-base font-semibold text-white shadow-[0_16px_32px_-18px_rgba(4,120,87,0.7)] transition active:translate-y-[1px] hover:bg-emerald-600";
const SECONDARY_BUTTON_CLASS =
  "rounded-full border border-emerald-200 bg-white px-4 py-2 text-base font-medium text-slate-700 transition active:translate-y-[1px] hover:border-emerald-300 hover:bg-emerald-50";
const GHOST_BUTTON_CLASS =
  "rounded-full border border-emerald-100 bg-emerald-50/70 px-4 py-2 text-base font-medium text-emerald-800 transition active:translate-y-[1px] hover:bg-emerald-100";
const METRIC_CARD_CLASS =
  "flex min-h-[118px] flex-col justify-between rounded-[24px] border border-emerald-100/80 bg-gradient-to-br from-white via-emerald-50/40 to-teal-50/70 p-4 shadow-[0_18px_40px_-28px_rgba(15,23,42,0.2)]";
const METRIC_LABEL_CLASS =
  "min-h-[2.75rem] text-xs font-semibold uppercase leading-snug tracking-wide text-emerald-700";
const METRIC_VALUE_CLASS = "mt-3 text-2xl font-semibold leading-none text-slate-900";
const ADMIN_FORCE_LOGIN_KEY = "admin_force_login";
const SECTION_ACCESS: Record<SectionKey, string> = {
  overview: "analytics:read",
  assessments: "assessments:read",
  rules: "rules:read",
  questionnaire: "questionnaire:read",
  users: "admin_users:read",
};
const DECISION_SIGNAL_LABELS: Record<string, string> = {
  timeline_adherence: "Timeline constraint pressure",
  budget_accuracy: "Budget constraint pressure",
  product_quality: "Quality assurance pressure",
  user_satisfaction: "User feedback need",
  communication_effectiveness: "Collaboration readiness",
  security_integration: "Security and assurance criticality",
  system_integration_effectiveness: "Integration and dependency complexity",
};

function formatStoredBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AdminPage() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();
  const [activeSection, setActiveSection] = useState<SectionKey>("overview");
  const [uiMode, setUiMode] = useState<"guided" | "advanced">("guided");
  const [assessmentViewMode, setAssessmentViewMode] = useState<"list" | "grouped">("list");
  const [assessmentSearch, setAssessmentSearch] = useState("");
  const [assessmentCompanyFilter, setAssessmentCompanyFilter] = useState("");
  const [assessmentRecommendationFilter, setAssessmentRecommendationFilter] = useState("");
  const [assessmentDocumentBackedOnly, setAssessmentDocumentBackedOnly] = useState(false);
  const [assessmentDateFrom, setAssessmentDateFrom] = useState("");
  const [assessmentDateTo, setAssessmentDateTo] = useState("");
  const [assessmentSortBy, setAssessmentSortBy] = useState("created_at");
  const [assessmentSortDir, setAssessmentSortDir] = useState<"asc" | "desc">("desc");
  const [assessmentListPage, setAssessmentListPage] = useState(1);
  const [assessmentGroupPage, setAssessmentGroupPage] = useState(1);
  const ASSESSMENT_PAGE_SIZE = 5;
  const [email, setEmail] = useState("admin@methodalign.local");
  const [password, setPassword] = useState("admin123");
  const [token, setToken] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [research, setResearch] = useState<ResearchMetrics | null>(null);
  const [researchQuestionnaireVersion, setResearchQuestionnaireVersion] = useState<number | null>(null);
  const [researchRulesVersion, setResearchRulesVersion] = useState<number | null>(null);
  const [assessmentWorkspaceAnalytics, setAssessmentWorkspaceAnalytics] = useState<AssessmentWorkspaceAnalytics | null>(null);
  const [assessments, setAssessments] = useState<AssessmentListItem[]>([]);
  const [groupedAssessments, setGroupedAssessments] = useState<CompanyGroupItem[]>([]);
  const [assessmentTotalPages, setAssessmentTotalPages] = useState({ list: 1, grouped: 1 });
  const [assessmentTotalRecords, setAssessmentTotalRecords] = useState({ list: 0, grouped: 0 });
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const [assessmentDeletingId, setAssessmentDeletingId] = useState<number | null>(null);
  const [deleteAssessmentPrompt, setDeleteAssessmentPrompt] = useState<{
    submissionId: number;
    summary: string;
  } | null>(null);
  const [incompleteActivityPrompt, setIncompleteActivityPrompt] = useState<IncompleteActivityData | null>(null);
  const [incompleteActivityLoading, setIncompleteActivityLoading] = useState(false);
  const [incompleteActivityDeleting, setIncompleteActivityDeleting] = useState(false);
  const [rules, setRules] = useState<Record<string, unknown> | null>(null);
  const [ruleVersions, setRuleVersions] = useState<Array<Record<string, unknown>>>([]);
  const [questionnaires, setQuestionnaires] = useState<Array<Record<string, unknown>>>([]);
  const [activeQuestionnaire, setActiveQuestionnaire] = useState<Record<string, unknown> | null>(null);
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [adminIdentity, setAdminIdentity] = useState<AdminIdentity | null>(null);
  const [canManageUsers, setCanManageUsers] = useState(false);
  const [canViewResearch, setCanViewResearch] = useState(false);
  const [canViewAssessments, setCanViewAssessments] = useState(false);
  const [canExportAssessments, setCanExportAssessments] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserRole, setNewUserRole] = useState("analyst");
  const [newUserFormError, setNewUserFormError] = useState<string | null>(null);
  const [creatingAdminUser, setCreatingAdminUser] = useState(false);
  const [note, setNote] = useState("Minor calibration update");
  const [questionnaireNote, setQuestionnaireNote] = useState("Questionnaire update");
  const [previewData, setPreviewData] = useState<RulePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [adminDataRefreshVersion, setAdminDataRefreshVersion] = useState(0);
  const [assessmentRefreshVersion, setAssessmentRefreshVersion] = useState(0);

  const resetAdminData = useCallback(() => {
    setSummary(null);
    setResearch(null);
    setResearchQuestionnaireVersion(null);
    setResearchRulesVersion(null);
    setAssessmentWorkspaceAnalytics(null);
    setAssessments([]);
    setGroupedAssessments([]);
    setAssessmentTotalPages({ list: 1, grouped: 1 });
    setAssessmentTotalRecords({ list: 0, grouped: 0 });
    setExpandedGroups({});
    setIncompleteActivityPrompt(null);
    setRules(null);
    setRuleVersions([]);
    setQuestionnaires([]);
    setActiveQuestionnaire(null);
    setAdminUsers([]);
    setAdminIdentity(null);
    setCanManageUsers(false);
    setCanViewResearch(false);
    setCanViewAssessments(false);
    setCanExportAssessments(false);
  }, []);

  const navigateToLogin = useCallback((message = "Your admin session has expired. Please sign in again.") => {
    window.localStorage.removeItem("admin_token");
    window.sessionStorage.setItem(ADMIN_FORCE_LOGIN_KEY, "1");
    resetAdminData();
    setToken(null);
    setSuccessMessage(null);
    setErrorMessage(message);
    router.replace("/admin");
  }, [resetAdminData, router]);

  const handleAdminRequestError = useCallback((error: unknown, fallbackMessage: string) => {
    if (isAdminUnauthenticated(error)) {
      navigateToLogin();
      return true;
    }
    setErrorMessage(error instanceof Error ? error.message : fallbackMessage);
    return false;
  }, [navigateToLogin]);

  useEffect(() => {
    let cancelled = false;
    const restoreToken = async () => {
      if (window.sessionStorage.getItem(ADMIN_FORCE_LOGIN_KEY) === "1") {
        return;
      }
      const existing = window.localStorage.getItem("admin_token");
      if (existing && !cancelled) {
        setToken(existing);
      }
    };
    void restoreToken();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const syncSectionFromUrl = () => {
      const requested = new URLSearchParams(window.location.search).get("section");
      if (requested && Object.prototype.hasOwnProperty.call(ADMIN_SECTION_LABELS, requested)) {
        const nextSection = requested as SectionKey;
        setActiveSection(nextSection);
        if (nextSection === "rules" || nextSection === "questionnaire" || nextSection === "users") {
          setUiMode("advanced");
        }
        return;
      }
      setActiveSection("overview");
    };
    syncSectionFromUrl();
    window.addEventListener("popstate", syncSectionFromUrl);
    return () => window.removeEventListener("popstate", syncSectionFromUrl);
  }, []);

  const navigateToSection = useCallback((section: SectionKey) => {
    setActiveSection(section);
    router.replace(section === "overview" ? "/admin?section=overview" : `/admin?section=${section}`, { scroll: false });
  }, [router]);

  useEffect(() => {
    if (!token) {
      return;
    }
    let cancelled = false;
    const loadAdminData = async () => {
      window.localStorage.setItem("admin_token", token);
      setLoading(true);
      setErrorMessage(null);
      try {
        const identity = await adminGet("/api/v1/admin/me", token) as AdminIdentity;
        if (cancelled) {
          return;
        }
        setAdminIdentity(identity);
        const permissions = new Set(identity.permissions);
        setCanManageUsers(permissions.has("admin_users:read") && permissions.has("admin_users:write"));
        setCanViewResearch(permissions.has("research:read"));
        setCanViewAssessments(permissions.has("assessments:read"));
        setCanExportAssessments(permissions.has("assessments:export"));

        const loaders: Array<Promise<void>> = [];
        if (permissions.has("analytics:read")) {
          loaders.push(adminGet("/api/v1/admin/analytics/summary", token).then((data) => {
            if (!cancelled) setSummary(data as Summary);
          }));
          loaders.push(adminGet("/api/v1/admin/assessments/analytics", token).then((data) => {
            if (!cancelled) setAssessmentWorkspaceAnalytics(data as AssessmentWorkspaceAnalytics);
          }));
        }
        if (permissions.has("research:read")) {
          loaders.push(adminGet("/api/v1/admin/analytics/research", token).then((data) => {
            if (!cancelled) {
              const metrics = data as ResearchMetrics;
              setResearch(metrics);
              setResearchQuestionnaireVersion(metrics.questionnaire_version);
              setResearchRulesVersion(metrics.rules_version);
            }
          }));
        }
        if (permissions.has("rules:read")) {
          loaders.push(adminGet("/api/v1/admin/rules", token).then((data) => {
            if (!cancelled) setRules(data as Record<string, unknown>);
          }));
          loaders.push(adminGet("/api/v1/admin/rules/versions", token).then((data) => {
            if (!cancelled) setRuleVersions(data as Array<Record<string, unknown>>);
          }));
        }
        if (permissions.has("questionnaire:read")) {
          loaders.push(adminGet("/api/v1/admin/questionnaires", token).then((data) => {
            const versions = data as Array<Record<string, unknown>>;
            if (!cancelled) {
              setQuestionnaires(versions);
              setActiveQuestionnaire(versions[0] ?? null);
            }
          }));
        }
        if (permissions.has("admin_users:read")) {
          loaders.push(adminGet("/api/v1/admin/users", token).then((data) => {
            if (!cancelled) setAdminUsers(data as AdminUser[]);
          }));
        }
        const results = await Promise.allSettled(loaders);
        if (!cancelled) {
          const rejected = results.filter((item) => item.status === "rejected") as Array<PromiseRejectedResult>;
          if (rejected.length > 0) {
            handleAdminRequestError(rejected[0].reason, "Some admin data failed to load.");
          }
        }
      } catch (error: unknown) {
        if (!cancelled) {
          handleAdminRequestError(error, "Unable to load your admin access.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void loadAdminData();
    return () => {
      cancelled = true;
    };
  }, [adminDataRefreshVersion, handleAdminRequestError, token]);

  useEffect(() => {
    if (!token || !adminIdentity?.permissions.includes("assessments:read")) {
      return;
    }
    let cancelled = false;
    const loadAssessments = async () => {
      const currentPage = assessmentViewMode === "list" ? assessmentListPage : assessmentGroupPage;
      const endpoint =
        assessmentViewMode === "list"
          ? "/api/v1/admin/assessments"
          : "/api/v1/admin/assessment-company-groups";
      const params = new URLSearchParams({
        page: String(currentPage),
        page_size: String(ASSESSMENT_PAGE_SIZE),
        sort_by: assessmentSortBy,
        sort_dir: assessmentSortDir,
      });
      if (assessmentSearch.trim()) {
        params.set("search", assessmentSearch.trim());
      }
      if (assessmentCompanyFilter.trim()) {
        params.set("company", assessmentCompanyFilter.trim());
      }
      if (assessmentRecommendationFilter) {
        params.set("recommendation", assessmentRecommendationFilter);
      }
      if (assessmentDocumentBackedOnly) {
        params.set("document_backed_only", "true");
      }
      if (assessmentDateFrom) {
        params.set("date_from", `${assessmentDateFrom}T00:00:00`);
      }
      if (assessmentDateTo) {
        params.set("date_to", `${assessmentDateTo}T23:59:59`);
      }
      try {
        const envelope = await adminGetEnvelope<PaginatedEnvelope<AssessmentListItem[] | CompanyGroupItem[]>>(
          `${endpoint}?${params.toString()}`,
          token
        );
        if (cancelled) {
          return;
        }
        const resolvedTotalPages = Math.max(1, envelope.total_pages);
        if (currentPage > resolvedTotalPages) {
          if (assessmentViewMode === "list") {
            setAssessmentListPage(resolvedTotalPages);
          } else {
            setAssessmentGroupPage(resolvedTotalPages);
          }
          return;
        }
        if (assessmentViewMode === "list") {
          setAssessments(envelope.data as AssessmentListItem[]);
        } else {
          setGroupedAssessments(envelope.data as CompanyGroupItem[]);
        }
        setAssessmentTotalPages((previous) => ({
          ...previous,
          [assessmentViewMode]: resolvedTotalPages,
        }));
        setAssessmentTotalRecords((previous) => ({
          ...previous,
          [assessmentViewMode]: envelope.total_records,
        }));
      } catch (error: unknown) {
        if (!cancelled) {
          handleAdminRequestError(error, "Assessment list failed to load.");
        }
      }
    };
    void loadAssessments();
    return () => {
      cancelled = true;
    };
  }, [
    ASSESSMENT_PAGE_SIZE,
    assessmentGroupPage,
    assessmentListPage,
    assessmentCompanyFilter,
    assessmentDateFrom,
    assessmentDateTo,
    assessmentDocumentBackedOnly,
    assessmentRecommendationFilter,
    assessmentRefreshVersion,
    assessmentSearch,
    assessmentSortBy,
    assessmentSortDir,
    assessmentViewMode,
    adminIdentity,
    handleAdminRequestError,
    token,
  ]);

  const submitLogin = async (event: FormEvent) => {
    event.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const auth = await adminLogin(email, password);
      window.sessionStorage.removeItem(ADMIN_FORCE_LOGIN_KEY);
      window.localStorage.setItem("admin_token", auth.access_token);
      setToken(auth.access_token);
      setSuccessMessage("Signed in.");
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : "Login failed.");
    }
  };

  const saveRules = async () => {
    if (!token || !rules) {
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const payload = (rules.payload ?? {}) as Record<string, unknown>;
      if (!window.confirm("Save a new rules version with current changes?")) {
        return;
      }
      const updated = await adminPut("/api/v1/admin/rules", token, { payload, change_note: note });
      setRules(updated as Record<string, unknown>);
      setSuccessMessage("Rules version saved.");
    } catch (error: unknown) {
      handleAdminRequestError(error, "Rule update failed.");
    }
  };

  const activateRuleVersion = async (version: number) => {
    if (!token) {
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      if (!window.confirm(`Activate rules version ${version}?`)) {
        return;
      }
      await adminPut("/api/v1/admin/rules/activate", token, { version });
      const [ruleData, versionData] = await Promise.all([
        adminGet("/api/v1/admin/rules", token),
        adminGet("/api/v1/admin/rules/versions", token),
      ]);
      setRules(ruleData as Record<string, unknown>);
      setRuleVersions(versionData as Array<Record<string, unknown>>);
      setSuccessMessage(`Rules v${version} activated.`);
    } catch (error: unknown) {
      handleAdminRequestError(error, "Rule activation failed.");
    }
  };

  const saveQuestionnaire = async () => {
    if (!token || !activeQuestionnaire) {
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      if (!window.confirm("Save a new questionnaire version with current changes?")) {
        return;
      }
      const payload = (activeQuestionnaire.payload ?? {}) as Record<string, unknown>;
      const title = String(activeQuestionnaire.title ?? "Questionnaire");
      await adminPut("/api/v1/admin/questionnaires", token, {
        title,
        payload,
        change_note: questionnaireNote,
      });
      const latest = (await adminGet("/api/v1/admin/questionnaires", token)) as Array<Record<string, unknown>>;
      setQuestionnaires(latest);
      setActiveQuestionnaire(latest[0] ?? null);
      setSuccessMessage("Questionnaire version saved.");
    } catch (error: unknown) {
      handleAdminRequestError(error, "Questionnaire update failed.");
    }
  };

  const activateQuestionnaireVersion = async (version: number) => {
    if (!token) {
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      if (!window.confirm(`Activate questionnaire version ${version}?`)) {
        return;
      }
      const updated = (await adminPut(
        `/api/v1/admin/questionnaires/activate/${version}`,
        token,
        {}
      )) as Record<string, unknown>;
      setActiveQuestionnaire(updated);
      setSuccessMessage(`Questionnaire v${version} activated.`);
    } catch (error: unknown) {
      handleAdminRequestError(error, "Questionnaire activation failed.");
    }
  };

  const createAdminUser = async () => {
    if (!token || creatingAdminUser) {
      return;
    }
    const normalizedEmail = newUserEmail.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setNewUserFormError("Enter a valid email address.");
      return;
    }
    if (newUserPassword.length < 8 || !newUserPassword.trim()) {
      setNewUserFormError("Password must contain at least 8 non-blank characters.");
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    setNewUserFormError(null);
    setCreatingAdminUser(true);
    try {
      await adminPost("/api/v1/admin/users", token, {
        email: normalizedEmail,
        password: newUserPassword,
        role: newUserRole,
      });
      const users = (await adminGet("/api/v1/admin/users", token)) as AdminUser[];
      setAdminUsers(users);
      setNewUserEmail("");
      setNewUserPassword("");
      setNewUserRole("analyst");
      setSuccessMessage("Admin user created.");
    } catch (error: unknown) {
      handleAdminRequestError(error, "Admin user creation failed.");
      setNewUserFormError(error instanceof Error ? error.message : "Admin user creation failed.");
    } finally {
      setCreatingAdminUser(false);
    }
  };

  const updateAdminUser = async (user: AdminUser, nextRole: string, nextActive: boolean) => {
    if (!token) {
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await adminPut(`/api/v1/admin/users/${user.id}`, token, {
        role: nextRole,
        is_active: nextActive,
      });
      const users = (await adminGet("/api/v1/admin/users", token)) as AdminUser[];
      setAdminUsers(users);
      setSuccessMessage("Admin user updated.");
    } catch (error: unknown) {
      handleAdminRequestError(error, "Admin user update failed.");
    }
  };

  const deleteAssessment = async (submissionId: number) => {
    if (!token || assessmentDeletingId === submissionId) {
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    setAssessmentDeletingId(submissionId);
    try {
      await adminDelete(`/api/v1/admin/assessments/${submissionId}`, token);
      setDeleteAssessmentPrompt(null);
      setAdminDataRefreshVersion((previous) => previous + 1);
      setAssessmentRefreshVersion((previous) => previous + 1);
      setSuccessMessage(`Assessment #${submissionId} deleted.`);
    } catch (error: unknown) {
      handleAdminRequestError(error, "Assessment delete failed.");
    } finally {
      setAssessmentDeletingId(null);
    }
  };

  const requestDeleteAssessment = (submissionId: number, summary: string) => {
    if (assessmentDeletingId === submissionId) {
      return;
    }
    setDeleteAssessmentPrompt({ submissionId, summary });
  };

  const requestIncompleteActivityReset = async () => {
    if (!token || incompleteActivityLoading) {
      return;
    }
    setIncompleteActivityLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const preview = (await adminGet(
        "/api/v1/admin/assessment-activity/incomplete",
        token
      )) as IncompleteActivityData;
      setIncompleteActivityPrompt(preview);
    } catch (error: unknown) {
      handleAdminRequestError(error, "Unable to inspect incomplete assessment activity.");
    } finally {
      setIncompleteActivityLoading(false);
    }
  };

  const resetIncompleteActivity = async () => {
    if (
      !token
      || !incompleteActivityPrompt
      || incompleteActivityDeleting
      || incompleteActivityPrompt.active_processing_jobs > 0
    ) {
      return;
    }
    setIncompleteActivityDeleting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const deleted = (await adminDelete(
        "/api/v1/admin/assessment-activity/incomplete",
        token,
        { confirmation: "RESET INCOMPLETE DATA" }
      )) as IncompleteActivityData;
      setIncompleteActivityPrompt(null);
      setAdminDataRefreshVersion((previous) => previous + 1);
      setAssessmentRefreshVersion((previous) => previous + 1);
      setSuccessMessage(
        deleted.file_cleanup_failures > 0
          ? `Incomplete records were deleted, but ${deleted.file_cleanup_failures} stored item(s) require server cleanup.`
          : `Cleared ${deleted.incomplete_sessions} incomplete session(s) and ${deleted.unsubmitted_drafts} unsubmitted draft(s).`
      );
    } catch (error: unknown) {
      handleAdminRequestError(error, "Incomplete activity reset failed.");
    } finally {
      setIncompleteActivityDeleting(false);
    }
  };

  const downloadCsv = async () => {
    if (!token) {
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/export.csv`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          navigateToLogin();
          return;
        }
        throw new Error("CSV export failed.");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "assessments.csv";
      anchor.click();
      window.URL.revokeObjectURL(url);
      setSuccessMessage("CSV exported.");
    } catch (error: unknown) {
      handleAdminRequestError(error, "CSV export failed.");
    }
  };

  const previewRules = async () => {
    if (!token || !rules) {
      return;
    }
    setPreviewLoading(true);
    setErrorMessage(null);
    try {
      const payload = (rules.payload ?? {}) as Record<string, unknown>;
      const data = (await adminPost("/api/v1/admin/rules/preview", token, { payload })) as RulePreview;
      setPreviewData(data);
      setSuccessMessage("Rule preview generated.");
    } catch (error: unknown) {
      handleAdminRequestError(error, "Rule preview failed.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const currentAssessmentPage = assessmentViewMode === "list" ? assessmentListPage : assessmentGroupPage;
  const currentAssessmentTotalPages = assessmentTotalPages[assessmentViewMode];
  const currentAssessmentTotalRecords = assessmentTotalRecords[assessmentViewMode];
  const canWriteAssessments = adminIdentity?.permissions.includes("assessments:write") ?? false;
  const canResetAssessmentData = adminIdentity?.permissions.includes("assessment_data:reset") ?? false;

  const sortAssessments = (column: string) => {
    if (assessmentViewMode === "list") {
      setAssessmentListPage(1);
    } else {
      setAssessmentGroupPage(1);
    }
    if (assessmentSortBy === column) {
      setAssessmentSortDir((previous) => (previous === "asc" ? "desc" : "asc"));
      return;
    }
    setAssessmentSortBy(column);
    setAssessmentSortDir(column === "created_at" || column === "latest_submission_at" ? "desc" : "asc");
  };

  const toggleGroupExpanded = (normalizedCompany: string) => {
    setExpandedGroups((previous) => ({
      ...previous,
      [normalizedCompany]: !previous[normalizedCompany],
    }));
  };
  const sectionTransition = prefersReducedMotion
    ? { duration: 0 }
    : { duration: 0.2, ease: "easeOut" as const };
  const sections: Array<{ key: SectionKey; label: string; advancedOnly: boolean }> = [
    { key: "overview", label: ADMIN_SECTION_LABELS.overview, advancedOnly: false },
    { key: "assessments", label: ADMIN_SECTION_LABELS.assessments, advancedOnly: false },
    { key: "rules", label: ADMIN_SECTION_LABELS.rules, advancedOnly: true },
    { key: "questionnaire", label: ADMIN_SECTION_LABELS.questionnaire, advancedOnly: true },
    { key: "users", label: ADMIN_SECTION_LABELS.users, advancedOnly: true },
  ];
  const visibleSections = sections.filter(
    (item) => (uiMode === "advanced" ? true : !item.advancedOnly)
      && (!adminIdentity || adminIdentity.permissions.includes(SECTION_ACCESS[item.key]))
  );
  const resolvedActiveSection = visibleSections.some((item) => item.key === activeSection)
    ? activeSection
    : (visibleSections[0]?.key ?? "overview");
  const activeTip = SECTION_TIPS[resolvedActiveSection];
  const activeSectionTitle = ADMIN_SECTION_LABELS[resolvedActiveSection];

  useEffect(() => {
    document.title = token ? adminPageTitle(resolvedActiveSection) : `${PRODUCT_NAME} | Admin Login`;
  }, [resolvedActiveSection, token]);

  const updateRuleNumber = (section: "construct_weights" | "agile_baseline" | "traditional_baseline", key: string, value: string) => {
    const parsed = Number(value);
    if (Number.isNaN(parsed) || !rules) {
      return;
    }
    setRules((previous) => {
      if (!previous) {
        return previous;
      }
      const payload = { ...(previous.payload as Record<string, unknown>) };
      const existing = ((payload[section] as Record<string, unknown>) ?? {});
      payload[section] = { ...existing, [key]: parsed };
      return { ...previous, payload };
    });
  };

  const updateRuleThreshold = (value: string) => {
    const parsed = Number(value);
    if (Number.isNaN(parsed) || !rules) {
      return;
    }
    setRules((previous) => {
      if (!previous) {
        return previous;
      }
      const payload = { ...(previous.payload as Record<string, unknown>) };
      payload.strictness_threshold = parsed;
      return { ...previous, payload };
    });
  };

  const updateRuleSetting = (key: "strictness_override_enabled" | "compatibility_normalization", value: boolean | string) => {
    setRules((previous) => {
      if (!previous) {
        return previous;
      }
      const payload = { ...(previous.payload as Record<string, unknown>), [key]: value };
      return { ...previous, payload };
    });
  };

  const loadResearchVersion = async (questionnaireVersion: number, rulesVersion: number) => {
    if (!token) {
      return;
    }
    setErrorMessage(null);
    try {
      const metrics = await adminGet(
        `/api/v1/admin/analytics/research?questionnaire_version=${questionnaireVersion}&rules_version=${rulesVersion}`,
        token
      ) as ResearchMetrics;
      setResearch(metrics);
      setResearchQuestionnaireVersion(metrics.questionnaire_version);
      setResearchRulesVersion(metrics.rules_version);
    } catch (error: unknown) {
      handleAdminRequestError(error, "Unable to load research metrics for the selected versions.");
    }
  };

  const updateDriverRule = (
    ruleKey: string,
    field: "construct" | "methodology" | "label" | "threshold",
    value: string
  ) => {
    if (!rules) {
      return;
    }
    setRules((previous) => {
      if (!previous) {
        return previous;
      }
      const payload = { ...(previous.payload as Record<string, unknown>) };
      const driverRules = {
        ...(((payload.driver_rules as Record<string, unknown>) ?? {}) as Record<string, Record<string, unknown>>),
      };
      const existing = { ...(driverRules[ruleKey] ?? {}) };
      existing[field] = field === "threshold" ? Number(value) : value;
      driverRules[ruleKey] = existing;
      payload.driver_rules = driverRules;
      return { ...previous, payload };
    });
  };

  const updateRiskRule = (
    ruleKey: string,
    field: "construct" | "metric" | "operator" | "label" | "threshold",
    value: string
  ) => {
    if (!rules) {
      return;
    }
    setRules((previous) => {
      if (!previous) {
        return previous;
      }
      const payload = { ...(previous.payload as Record<string, unknown>) };
      const riskRules = {
        ...(((payload.risk_flag_rules as Record<string, unknown>) ?? {}) as Record<string, Record<string, unknown>>),
      };
      const existing = { ...(riskRules[ruleKey] ?? {}) };
      existing[field] = field === "threshold" ? Number(value) : value;
      riskRules[ruleKey] = existing;
      payload.risk_flag_rules = riskRules;
      return { ...previous, payload };
    });
  };

  const questionnairePayload = ((activeQuestionnaire?.payload ?? {
    profile_questions: [],
    likert_questions: [],
    document_questions: [],
  }) as QuestionnairePayload);

  const updateQuestionnairePayload = (payload: QuestionnairePayload) => {
    setActiveQuestionnaire((previous) => {
      if (!previous) {
        return previous;
      }
      return { ...previous, payload };
    });
  };

  const updateProfileQuestion = (index: number, patch: Partial<ProfileQuestion>) => {
    const next = [...questionnairePayload.profile_questions];
    next[index] = { ...next[index], ...patch };
    updateQuestionnairePayload({ ...questionnairePayload, profile_questions: next });
  };

  const updateLikertQuestion = (index: number, patch: Partial<LikertQuestion>) => {
    const next = [...questionnairePayload.likert_questions];
    next[index] = { ...next[index], ...patch };
    updateQuestionnairePayload({ ...questionnairePayload, likert_questions: next });
  };

  const updateLikertScaleLabel = (questionIndex: number, labelIndex: number, value: string) => {
    const question = questionnairePayload.likert_questions[questionIndex];
    const labels = [...(question.scale_labels ?? DEFAULT_LIKERT_SCALE_LABELS)] as LikertQuestion["scale_labels"];
    labels[labelIndex] = value;
    updateLikertQuestion(questionIndex, { scale_labels: labels });
  };

  const updateDocumentQuestion = (index: number, patch: Partial<DocumentQuestion>) => {
    const next = [...questionnairePayload.document_questions];
    next[index] = { ...next[index], ...patch };
    updateQuestionnairePayload({ ...questionnairePayload, document_questions: next });
  };

  const moveItem = <T,>(list: T[], index: number, direction: -1 | 1): T[] => {
    const target = index + direction;
    if (target < 0 || target >= list.length) {
      return list;
    }
    const next = [...list];
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    return next;
  };

  const addProfileQuestion = () => {
    const next: ProfileQuestion = {
      question_id: `Q${Date.now()}`,
      kind: "text",
      profile_key: "name",
      prompt: "New profile question",
      placeholder: "",
      options: null,
      document_extraction: {
        enabled: false,
        instruction: "Extract a direct answer only when the document contains supporting evidence.",
        answer_type: "text",
        rubric: null,
      },
    };
    updateQuestionnairePayload({
      ...questionnairePayload,
      profile_questions: [...questionnairePayload.profile_questions, next],
    });
  };

  const addLikertQuestion = () => {
    const next: LikertQuestion = {
      question_id: `Q${Date.now()}`,
      construct: "FLEXIBILITY",
      prompt: "New likert question",
      scale_labels: [...DEFAULT_LIKERT_SCALE_LABELS],
      document_extraction: {
        enabled: false,
        instruction: "This user-reported question is not extracted from documents.",
        answer_type: "likert",
        rubric: "This user-reported question is not extracted from documents.",
      },
    };
    updateQuestionnairePayload({
      ...questionnairePayload,
      likert_questions: [...questionnairePayload.likert_questions, next],
    });
  };

  const addDocumentQuestion = () => {
    const next: DocumentQuestion = {
      question_id: `D${Date.now()}`,
      construct: "FLEXIBILITY",
      prompt: "New document-only question",
      weight: 1,
      document_extraction: {
        enabled: true,
        instruction: "Use only direct, cited document evidence. Do not infer missing facts.",
        answer_type: "likert",
        rubric: "1 means explicit low or absent evidence, 3 means bounded or mixed evidence, and 5 means explicit high, fixed, or mandatory evidence. Return no answer when unsupported.",
      },
    };
    updateQuestionnairePayload({
      ...questionnairePayload,
      document_questions: [...questionnairePayload.document_questions, next],
    });
  };

  if (!token) {
    return (
      <main className={`flex min-h-[100dvh] items-center px-6 ${SHELL_BACKGROUND}`}>
        <div className="mx-auto grid w-full max-w-5xl gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <section className="space-y-5">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-800 shadow-[0_10px_30px_-20px_rgba(4,120,87,0.45)]">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Admin workspace
            </div>
            <div className="space-y-3">
              <h1 className="max-w-lg text-4xl font-semibold tracking-tight text-slate-950 md:text-5xl">
                Review assessments, evidence, and configuration in one place.
              </h1>
              <p className="max-w-xl text-base leading-7 text-slate-600">
                The admin dashboard is structured for assessment operations first: submissions, document-backed runs,
                AI evidence, and rules governance.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className={METRIC_CARD_CLASS}>
                <p className={METRIC_LABEL_CLASS}>Assessment workspace</p>
                <p className="mt-3 text-lg font-semibold leading-snug text-slate-900">Funnel, documents, and review detail</p>
              </div>
              <div className={METRIC_CARD_CLASS}>
                <p className={METRIC_LABEL_CLASS}>Configuration control</p>
                <p className="mt-3 text-lg font-semibold leading-snug text-slate-900">Rules, questionnaire, and admin access</p>
              </div>
            </div>
          </section>
          <form onSubmit={submitLogin} className={`w-full space-y-5 p-7 ${PANEL_CLASS}`}>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-emerald-700">{PRODUCT_NAME}</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">Admin Login</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">Use the admin account to access assessments, analytics, and configuration tools.</p>
            </div>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              <span>Email</span>
              <input
                id="admin-login-email"
                name="email"
                autoComplete="username"
                className={INPUT_CLASS}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              <span>Password</span>
              <input
                id="admin-login-password"
                name="password"
                autoComplete="current-password"
                className={INPUT_CLASS}
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <button className={PRIMARY_BUTTON_CLASS} type="submit">Sign In</button>
          </form>
        </div>
      </main>
    );
  }

  return (
    <AdminWorkspaceShell
      activeSection={resolvedActiveSection}
      sections={visibleSections}
      uiMode={uiMode}
      onNavigate={navigateToSection}
      onToggleUiMode={() => {
        const next = uiMode === "guided" ? "advanced" : "guided";
        setUiMode(next);
        if (next === "guided" && (activeSection === "rules" || activeSection === "questionnaire" || activeSection === "users")) {
          navigateToSection("overview");
        }
      }}
      canExport={canExportAssessments}
      onExport={downloadCsv}
      onSignOut={() => {
        window.localStorage.removeItem("admin_token");
        window.sessionStorage.setItem(ADMIN_FORCE_LOGIN_KEY, "1");
        resetAdminData();
        setToken(null);
        setSuccessMessage(null);
        setErrorMessage(null);
      }}
    >
      <div className="min-h-full bg-slate-50 px-4 py-5 sm:px-6 lg:px-8 xl:px-10">
      <div className="space-y-5 pb-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">{PRODUCT_NAME} Admin</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">{activeSectionTitle}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Assessment operations, evidence review, and administrative configuration.</p>
        </div>
      </header>
      {loading ? (
        <section className={`${SOFT_PANEL_CLASS} p-4 text-base text-slate-600`}>
          Loading admin data...
        </section>
      ) : null}

      {errorMessage ? (
        <section className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-base text-rose-700">
          {errorMessage}
        </section>
      ) : null}

      {successMessage ? (
        <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-base text-emerald-700">
          {successMessage}
        </section>
      ) : null}

      <section className={`overflow-hidden p-5 text-slate-800 ${SOFT_PANEL_CLASS}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">Operator note</p>
            <p className="mt-2 text-xl font-semibold">{activeTip.title}</p>
            <p className="mt-2 max-w-3xl text-base leading-7 text-slate-600">{activeTip.body}</p>
          </div>
          <div className="rounded-2xl border border-emerald-100 bg-white/80 px-4 py-3 text-sm font-medium text-slate-600 shadow-[0_12px_28px_-24px_rgba(15,23,42,0.25)]">
            Tip: {activeTip.note}
          </div>
        </div>
      </section>

      {summary && resolvedActiveSection === "overview" ? (
        <motion.section
          initial={{ opacity: 0, y: prefersReducedMotion ? 0 : 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={sectionTransition}
          className={`min-h-[520px] space-y-4 p-5 ${PANEL_CLASS}`}
        >
          <div className="grid gap-4 md:grid-cols-3">
          <div className={METRIC_CARD_CLASS}>
            <p className={METRIC_LABEL_CLASS}>Total Assessments</p>
            <p className={METRIC_VALUE_CLASS}>{summary.total_submissions}</p>
          </div>
          <div className={METRIC_CARD_CLASS}>
            <p className={METRIC_LABEL_CLASS}>Agile Recommendations</p>
            <p className="mt-3 text-2xl font-semibold leading-none text-emerald-700">{summary.agile_recommendations}</p>
          </div>
          <div className={METRIC_CARD_CLASS}>
            <p className={METRIC_LABEL_CLASS}>Traditional Recommendations</p>
            <p className="mt-3 text-2xl font-semibold leading-none text-teal-700">{summary.traditional_recommendations}</p>
          </div>
          </div>
          {uiMode === "advanced" && canViewResearch && research ? (
            <div className={`p-5 ${SOFT_PANEL_CLASS}`}>
          <h2 className="text-xl font-semibold text-slate-800">Research Metrics</h2>
          <p className="mt-2 text-base text-slate-600">
            Metrics are isolated by questionnaire and scoring-rule version so incompatible instruments are never pooled.
          </p>
          <div className="mt-3 grid gap-3 rounded-2xl border border-emerald-100 bg-white/80 p-3 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">
              Questionnaire version
              <select
                className={`${INPUT_CLASS} mt-1`}
                value={researchQuestionnaireVersion ?? research.questionnaire_version}
                onChange={(event) => {
                  const nextQuestionnaireVersion = Number(event.target.value);
                  void loadResearchVersion(
                    nextQuestionnaireVersion,
                    researchRulesVersion ?? research.rules_version
                  );
                }}
              >
                {questionnaires.map((item) => (
                  <option key={Number(item.version)} value={Number(item.version)}>
                    Version {Number(item.version)}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700">
              Rules version
              <select
                className={`${INPUT_CLASS} mt-1`}
                value={researchRulesVersion ?? research.rules_version}
                onChange={(event) => {
                  const nextRulesVersion = Number(event.target.value);
                  void loadResearchVersion(
                    researchQuestionnaireVersion ?? research.questionnaire_version,
                    nextRulesVersion
                  );
                }}
              >
                {ruleVersions.map((item) => (
                  <option key={Number(item.version)} value={Number(item.version)}>
                    Version {Number(item.version)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <p className="mt-3 text-base text-slate-600">Sample size: {research.sample_size}</p>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-slate-100 p-3">
              <p className="text-base font-semibold text-slate-700">Cronbach Alpha</p>
              <div className="mt-2 space-y-2">
                {Object.entries(research.cronbach_alpha).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-base">
                    <span className="font-medium text-slate-600">{key}</span>
                    <span className="text-slate-800">{value ?? "n/a"}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-slate-100 p-3">
              <p className="text-base font-semibold text-slate-700">Construct Means</p>
              <div className="mt-2 space-y-3">
                {Object.entries(research.construct_score_means).map(([key, value]) => (
                  <div key={key}>
                    <div className="flex items-center justify-between text-base">
                      <span className="font-medium text-slate-600">{key}</span>
                      <span className="text-slate-800">{value.toFixed(2)}</span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-slate-100">
                      <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${Math.min(100, value * 20)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-3 rounded-lg border border-slate-100 p-3">
            <p className="text-base font-semibold text-slate-700">Correlations</p>
            <div className="mt-2 space-y-2">
              {Object.entries(research.correlations).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-base">
                  <span className="font-medium text-slate-600">{key}</span>
                  <span className="text-slate-800">{value ?? "n/a"}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-3 rounded-lg border border-slate-100 p-3">
            <p className="text-base font-semibold text-slate-700">Independent Sample t-Tests (Welch)</p>
            <div className="mt-2 space-y-3">
              {Object.entries(research.t_tests).map(([name, values]) => (
                <div key={name} className="rounded-md border border-slate-100 p-2">
                  <p className="text-base font-semibold text-slate-700">{name}</p>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-base text-slate-600">
                    {Object.entries(values).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between gap-3">
                        <span>{key}</span>
                        <span className="font-medium text-slate-800">{value ?? "n/a"}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-3 rounded-lg border border-slate-100 p-3">
            <p className="text-base font-semibold text-slate-700">Decision Signal Means (7 Derived Signals)</p>
            <p className="mt-1 text-sm text-slate-500">
              These are derived from assessment answers for decision support; they are not independently observed project outcomes.
            </p>
            <div className="mt-2 space-y-3">
              {Object.entries(research.dependent_variable_means).map(([group, values]) => (
                <div key={group} className="rounded-md border border-slate-100 p-2">
                  <p className="text-base font-semibold capitalize text-slate-700">{group.replaceAll("_", " ")}</p>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-base text-slate-600">
                    {Object.entries(values).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between gap-3">
                        <span>{DECISION_SIGNAL_LABELS[key] ?? key}</span>
                        <span className="font-medium text-slate-800">{value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-slate-100 p-3">
              <p className="text-base font-semibold text-slate-700">Confidence Distribution</p>
              <div className="mt-2 space-y-2">
                {Object.entries(research.confidence_distribution).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-base">
                    <span className="font-medium capitalize text-slate-600">{key}</span>
                    <span className="text-slate-800">{value}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-slate-100 p-3">
              <p className="text-base font-semibold text-slate-700">Triggered Risk Flags</p>
              <div className="mt-2 space-y-2">
                {Object.keys(research.risk_flag_counts).length > 0 ? (
                  Object.entries(research.risk_flag_counts).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-base">
                      <span className="font-medium text-slate-600">{key}</span>
                      <span className="text-slate-800">{value}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-base text-slate-500">No risk flags recorded yet.</p>
                )}
              </div>
            </div>
          </div>
          <div className="mt-3 grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-slate-100 p-3">
              <p className="text-base font-semibold text-slate-700">Hybrid Readiness</p>
              <div className="mt-2 space-y-2">
                {Object.entries(research.hybrid_readiness_distribution).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-base">
                    <span className="font-medium capitalize text-slate-600">{key}</span>
                    <span className="text-slate-800">{value}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-slate-100 p-3">
              <p className="text-base font-semibold text-slate-700">Delivery Strategies</p>
              <div className="mt-2 space-y-2">
                {Object.keys(research.delivery_strategy_distribution).length > 0 ? (
                  Object.entries(research.delivery_strategy_distribution).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between gap-3 text-base">
                      <span className="font-medium text-slate-600">{key.replaceAll("_", " ")}</span>
                      <span className="text-slate-800">{value}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-base text-slate-500">No strategy profiles recorded yet.</p>
                )}
              </div>
            </div>
            <div className="rounded-lg border border-slate-100 p-3">
              <p className="text-base font-semibold text-slate-700">Advisory Practices</p>
              <div className="mt-2 space-y-2">
                {Object.keys(research.strategy_option_counts).length > 0 ? (
                  Object.entries(research.strategy_option_counts).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-base">
                      <span className="font-medium text-slate-600">{key.replaceAll("_", " ")}</span>
                      <span className="text-slate-800">{value}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-base text-slate-500">No advisory practices recorded yet.</p>
                )}
              </div>
            </div>
          </div>
          <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50/40 p-3">
            <p className="text-base font-semibold text-slate-700">Document Evidence Adjustment</p>
            <p className="mt-1 text-sm text-slate-600">Kept separate from questionnaire reliability metrics. Confirmed evidence can contribute at most {(research.evidence_adjusted.maximum_construct_contribution * 100).toFixed(0)}% of a construct score.</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Documented</p><p className="mt-1 text-xl font-semibold text-slate-800">{research.evidence_adjusted.documented_assessments}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Adjusted scores</p><p className="mt-1 text-xl font-semibold text-slate-800">{research.evidence_adjusted.assessments_with_score_adjustment}</p></div>
              {Object.entries(research.evidence_adjusted.average_coverage).map(([key, value]) => <div key={key}><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{key} coverage</p><p className="mt-1 text-xl font-semibold text-slate-800">{(value * 100).toFixed(0)}%</p></div>)}
            </div>
          </div>
            </div>
          ) : null}
        </motion.section>
      ) : null}

      {canViewAssessments && resolvedActiveSection === "assessments" ? (
        <motion.section
          initial={{ opacity: 0, y: prefersReducedMotion ? 0 : 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={sectionTransition}
          className={`min-h-[520px] space-y-5 p-5 ${PANEL_CLASS}`}
        >
          {assessmentWorkspaceAnalytics ? (
            <>
              <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
                <section className={SOFT_PANEL_CLASS + " p-4"}>
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Assessment Funnel</p>
                      <h2 className="mt-1 text-xl font-semibold text-slate-800">Progress and completion</h2>
                    </div>
                    <div className="rounded-2xl border border-emerald-100 bg-white px-3 py-3 text-right shadow-[0_16px_30px_-24px_rgba(15,23,42,0.24)]">
                      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Completion Rate</p>
                      <p className="text-2xl font-semibold text-slate-900">{assessmentWorkspaceAnalytics.completion_rate.toFixed(2)}%</p>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
                    {[
                      ["Opened", assessmentWorkspaceAnalytics.opened_assessments],
                      ["Answered", assessmentWorkspaceAnalytics.answered_assessments],
                      ["All Questions", assessmentWorkspaceAnalytics.fully_answered_assessments],
                      ["In Progress", assessmentWorkspaceAnalytics.in_progress_assessments],
                      ["Submitted", assessmentWorkspaceAnalytics.completed_submissions],
                      ["Drafts", assessmentWorkspaceAnalytics.draft_created_count],
                    ].map(([label, value]) => (
                      <div key={String(label)} className={METRIC_CARD_CLASS}>
                        <p className={METRIC_LABEL_CLASS}>{label}</p>
                        <p className={METRIC_VALUE_CLASS}>{value}</p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className={SOFT_PANEL_CLASS + " p-4"}>
                  <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">Assessment Intelligence</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className={METRIC_CARD_CLASS}>
                      <p className={METRIC_LABEL_CLASS}>Document-backed</p>
                      <p className={METRIC_VALUE_CLASS}>{assessmentWorkspaceAnalytics.document_backed_assessments}</p>
                    </div>
                    <div className={METRIC_CARD_CLASS}>
                      <p className={METRIC_LABEL_CLASS}>Uploaded Docs</p>
                      <p className={METRIC_VALUE_CLASS}>{assessmentWorkspaceAnalytics.uploaded_document_count}</p>
                    </div>
                    <div className={METRIC_CARD_CLASS}>
                      <p className={METRIC_LABEL_CLASS}>Processed Docs</p>
                      <p className={METRIC_VALUE_CLASS}>{assessmentWorkspaceAnalytics.total_documents_processed}</p>
                    </div>
                    <div className={METRIC_CARD_CLASS}>
                      <p className={METRIC_LABEL_CLASS}>Avg Trace Steps</p>
                      <p className={METRIC_VALUE_CLASS}>{assessmentWorkspaceAnalytics.average_trace_steps.toFixed(2)}</p>
                    </div>
                    <div className={METRIC_CARD_CLASS}>
                      <p className={METRIC_LABEL_CLASS}>Ready Jobs</p>
                      <p className={METRIC_VALUE_CLASS}>{assessmentWorkspaceAnalytics.processing_ready_count}</p>
                    </div>
                    <div className={METRIC_CARD_CLASS}>
                      <p className={METRIC_LABEL_CLASS}>Confirmed Evidence</p>
                      <p className={METRIC_VALUE_CLASS}>{assessmentWorkspaceAnalytics.evidence_confirmed_count}</p>
                    </div>
                  </div>
                </section>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <section className={SOFT_PANEL_CLASS + " p-4"}>
                  <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">Stage Frequency</p>
                  <div className="mt-4 space-y-3">
                    {Object.entries(assessmentWorkspaceAnalytics.stage_frequency).map(([key, value]) => (
                      <div key={key}>
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium text-slate-700">{key}</span>
                          <span className="text-slate-500">{value}</span>
                        </div>
                        <div className="mt-1 h-2 rounded-full bg-slate-100">
                          <div className="h-2 rounded-full bg-emerald-600" style={{ width: `${Math.min(100, value * 12)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <section className={SOFT_PANEL_CLASS + " p-4"}>
                  <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">Evidence Quality</p>
                  <div className="mt-4 space-y-2">
                    {[
                      ["Evidence suggestions", assessmentWorkspaceAnalytics.evidence_suggested_count],
                      ["Neutral fallbacks", assessmentWorkspaceAnalytics.neutral_fallback_count],
                      ["Failed jobs", assessmentWorkspaceAnalytics.processing_failed_count],
                    ].map(([label, value]) => (
                      <div key={String(label)} className="flex items-center justify-between rounded-2xl border border-emerald-100 bg-white px-3 py-2 text-sm shadow-[0_16px_30px_-24px_rgba(15,23,42,0.18)]">
                        <span className="font-medium text-slate-700">{label}</span>
                        <span className="text-slate-500">{value}</span>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </>
          ) : null}

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-4">
              <h2 className="text-xl font-semibold text-slate-800">Assessments</h2>
              <div className="flex items-center rounded-full border border-emerald-100 bg-emerald-50/70 p-1">
                <button
                  type="button"
                  className={["rounded-full px-3 py-1 text-sm font-medium transition-colors", assessmentViewMode === "list" ? "bg-white shadow-sm text-slate-900" : "text-slate-500 hover:text-slate-700"].join(" ")}
                  onClick={() => setAssessmentViewMode("list")}
                >
                  List View
                </button>
                <button
                  type="button"
                  className={["rounded-full px-3 py-1 text-sm font-medium transition-colors", assessmentViewMode === "grouped" ? "bg-white shadow-sm text-slate-900" : "text-slate-500 hover:text-slate-700"].join(" ")}
                  onClick={() => setAssessmentViewMode("grouped")}
                >
                  Grouped by Company
                </button>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <p className="text-sm text-slate-500">
                Showing page {currentAssessmentPage} of {currentAssessmentTotalPages} · {currentAssessmentTotalRecords} records
              </p>
              {canResetAssessmentData ? (
                <button
                  type="button"
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-rose-600 bg-white px-2.5 py-1.5 text-sm font-semibold text-rose-700 transition hover:bg-rose-50 active:scale-[0.98] disabled:opacity-50"
                  onClick={() => void requestIncompleteActivityReset()}
                  disabled={incompleteActivityLoading || incompleteActivityDeleting}
                  aria-label="Clear incomplete assessment activity"
                  title="Clear incomplete assessment activity"
                >
                  <Trash size={14} />
                  {incompleteActivityLoading ? "Checking" : "Clear"}
                </button>
              ) : null}
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-[1.25fr_1fr_0.9fr_0.9fr_0.9fr_auto]">
            <input
              id="assessment-search"
              name="assessment_search"
              autoComplete="off"
              placeholder="Search name, company, project, recommendation"
              className={INPUT_CLASS}
              value={assessmentSearch}
              onChange={(event) => {
                setAssessmentSearch(event.target.value);
                setAssessmentListPage(1);
                setAssessmentGroupPage(1);
              }}
            />
            <input
              id="assessment-company-filter"
              name="assessment_company_filter"
              autoComplete="off"
              placeholder="Filter company"
              className={INPUT_CLASS}
              value={assessmentCompanyFilter}
              onChange={(event) => {
                setAssessmentCompanyFilter(event.target.value);
                setAssessmentListPage(1);
                setAssessmentGroupPage(1);
              }}
            />
            <select
              className={INPUT_CLASS}
              value={assessmentRecommendationFilter}
              onChange={(event) => {
                setAssessmentRecommendationFilter(event.target.value);
                setAssessmentListPage(1);
                setAssessmentGroupPage(1);
              }}
            >
              <option value="">All methods</option>
              <option value="Agile">Agile</option>
              <option value="Traditional">Traditional</option>
            </select>
            <input
              type="date"
              className={INPUT_CLASS}
              value={assessmentDateFrom}
              onChange={(event) => {
                setAssessmentDateFrom(event.target.value);
                setAssessmentListPage(1);
                setAssessmentGroupPage(1);
              }}
            />
            <input
              type="date"
              className={INPUT_CLASS}
              value={assessmentDateTo}
              onChange={(event) => {
                setAssessmentDateTo(event.target.value);
                setAssessmentListPage(1);
                setAssessmentGroupPage(1);
              }}
            />
            <label className="flex items-center gap-2 rounded-2xl border border-emerald-100 bg-white px-3 py-2 text-sm text-slate-700 shadow-[0_12px_28px_-24px_rgba(15,23,42,0.2)]">
              <input
                type="checkbox"
                checked={assessmentDocumentBackedOnly}
                onChange={(event) => {
                  setAssessmentDocumentBackedOnly(event.target.checked);
                  setAssessmentListPage(1);
                  setAssessmentGroupPage(1);
                }}
              />
              Docs only
            </label>
          </div>
        {assessmentViewMode === "list" ? (
          <div className="mt-3 max-h-[420px] overflow-auto rounded-lg border border-slate-100">
            <table className="min-w-full text-left text-base">
              <thead className="sticky top-0 z-10 bg-white">
                <tr className="text-slate-500">
                  <th className="py-2">
                    <button type="button" className="font-medium" onClick={() => sortAssessments("name")}>
                      Name {assessmentSortBy === "name" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="font-medium" onClick={() => sortAssessments("company")}>
                      Company {assessmentSortBy === "company" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="font-medium" onClick={() => sortAssessments("project_name")}>
                      Project {assessmentSortBy === "project_name" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="font-medium" onClick={() => sortAssessments("recommendation")}>
                      Recommendation {assessmentSortBy === "recommendation" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>Docs</th>
                  <th>
                    <button type="button" className="font-medium" onClick={() => sortAssessments("created_at")}>
                      Submitted {assessmentSortBy === "created_at" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th className="sticky right-0 z-10 bg-white pr-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {assessments.map((item) => (
                  <tr key={item.submission_id} className="border-t border-slate-100">
                    <td className="py-2">{item.name}</td>
                    <td>{item.company}</td>
                    <td>{item.project_name}</td>
                    <td>{item.recommendation}</td>
                    <td>{item.has_documents ? "Yes" : "No"}</td>
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                    <td className="sticky right-0 bg-white pr-3">
                      <div className="flex min-w-[220px] justify-end gap-2">
                        <button
                          type="button"
                          className={`${SECONDARY_BUTTON_CLASS} px-3 py-1 text-sm disabled:opacity-50`}
                          onClick={() => router.push(`/admin/assessments/${item.submission_id}`)}
                          disabled={assessmentDeletingId === item.submission_id}
                        >
                          View details
                        </button>
                        {canWriteAssessments ? <button
                          type="button"
                          className="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-sm font-medium text-rose-700 shadow-[0_12px_28px_-22px_rgba(244,63,94,0.8)] transition hover:bg-rose-100 disabled:opacity-50"
                          onClick={() => requestDeleteAssessment(item.submission_id, `${item.name} | ${item.company} | ${item.project_name}`)}
                          disabled={assessmentDeletingId === item.submission_id}
                        >
                          <Trash size={14} />
                          {assessmentDeletingId === item.submission_id ? "Deleting" : "Delete"}
                        </button> : null}
                      </div>
                    </td>
                  </tr>
                ))}
                {assessments.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-4 text-center text-slate-500">No assessments found.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="mt-3 max-h-[420px] overflow-auto rounded-lg border border-slate-100">
            <table className="min-w-full text-left text-base">
              <thead className="sticky top-0 z-10 bg-white">
                <tr className="text-slate-500">
                  <th className="py-2 pl-3">
                    <button type="button" className="font-medium" onClick={() => sortAssessments("company")}>
                      Company {assessmentSortBy === "company" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="font-medium" onClick={() => sortAssessments("submission_count")}>
                      Submissions {assessmentSortBy === "submission_count" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>Agile</th>
                  <th>Traditional</th>
                  <th>
                    <button type="button" className="font-medium" onClick={() => sortAssessments("avg_agile_score")}>
                      Avg Agile {assessmentSortBy === "avg_agile_score" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="font-medium" onClick={() => sortAssessments("avg_traditional_score")}>
                      Avg Trad {assessmentSortBy === "avg_traditional_score" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="font-medium" onClick={() => sortAssessments("latest_submission_at")}>
                      Latest {assessmentSortBy === "latest_submission_at" ? (assessmentSortDir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </th>
                  <th>Docs</th>
                  <th className="sticky right-0 z-10 bg-white pr-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {groupedAssessments.map((group) => {
                  const isExpanded = Boolean(expandedGroups[group.normalized_company]);
                  const documentBackedCount = group.items.filter((item) => item.has_documents).length;
                  return (
                    <Fragment key={group.normalized_company}>
                      <tr className="border-t border-slate-100">
                        <td className="py-2 pl-3 font-medium text-slate-800">
                          <button
                            type="button"
                            className="inline-flex items-center gap-2 text-left"
                            onClick={() => toggleGroupExpanded(group.normalized_company)}
                          >
                            <span className="text-slate-500">{isExpanded ? "−" : "+"}</span>
                            <span>{group.company}</span>
                          </button>
                        </td>
                        <td>{group.submission_count}</td>
                        <td className="text-emerald-700">{group.agile_count}</td>
                        <td className="text-slate-600">{group.traditional_count}</td>
                        <td>{group.avg_agile_score.toFixed(1)}</td>
                        <td>{group.avg_traditional_score.toFixed(1)}</td>
                        <td className="text-sm">{new Date(group.latest_submission_at).toLocaleDateString()}</td>
                        <td className="text-sm text-slate-600">
                          {documentBackedCount > 0 ? `${documentBackedCount}/${group.submission_count}` : "0"}
                        </td>
                        <td className="sticky right-0 bg-white pr-3 text-right text-sm text-slate-500">
                          {isExpanded ? "Expanded" : "Expand"}
                        </td>
                      </tr>
                      {isExpanded ? (
                        group.items.map((item) => (
                          <tr key={item.submission_id} className="border-t border-slate-50 bg-slate-50/70">
                            <td className="py-2 pl-10 text-sm text-slate-700">{item.name}</td>
                            <td className="text-sm text-slate-600">{item.project_name}</td>
                            <td className="text-sm text-emerald-700">{item.recommendation === "Agile" ? 1 : 0}</td>
                            <td className="text-sm text-slate-600">{item.recommendation === "Traditional" ? 1 : 0}</td>
                            <td className="text-sm text-slate-600">{item.agile_score.toFixed(1)}</td>
                            <td className="text-sm text-slate-600">{item.traditional_score.toFixed(1)}</td>
                            <td className="text-sm text-slate-600">{new Date(item.created_at).toLocaleDateString()}</td>
                            <td className="text-sm text-slate-600">{item.has_documents ? "Docs" : "No docs"}</td>
                            <td className="sticky right-0 bg-slate-50/95 py-2 pr-3">
                              <div className="flex min-w-[220px] justify-end gap-2">
                                <button
                                  type="button"
                                  className={`${SECONDARY_BUTTON_CLASS} px-3 py-1 text-sm disabled:opacity-50`}
                                  onClick={() => router.push(`/admin/assessments/${item.submission_id}`)}
                                  disabled={assessmentDeletingId === item.submission_id}
                                >
                                  View details
                                </button>
                                {canWriteAssessments ? <button
                                  type="button"
                                  className="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-sm font-medium text-rose-700 shadow-[0_12px_28px_-22px_rgba(244,63,94,0.8)] transition hover:bg-rose-100 disabled:opacity-50"
                                  onClick={() => requestDeleteAssessment(item.submission_id, `${item.name} | ${group.company} | ${item.project_name}`)}
                                  disabled={assessmentDeletingId === item.submission_id}
                                >
                                  <Trash size={14} />
                                  {assessmentDeletingId === item.submission_id ? "Deleting" : "Delete"}
                                </button> : null}
                              </div>
                            </td>
                          </tr>
                        ))
                      ) : null}
                    </Fragment>
                  );
                })}
                {groupedAssessments.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-4 text-center text-slate-500">No grouped data available.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-3 flex items-center justify-end gap-2">
          <button
            type="button"
            className={`${SECONDARY_BUTTON_CLASS} px-3 py-1 disabled:opacity-50`}
            onClick={() =>
              assessmentViewMode === "list"
                ? setAssessmentListPage((previous) => Math.max(1, previous - 1))
                : setAssessmentGroupPage((previous) => Math.max(1, previous - 1))
            }
            disabled={currentAssessmentPage <= 1}
          >
            Prev
          </button>
          <span className="text-base text-slate-500">
            Page {currentAssessmentPage} / {currentAssessmentTotalPages}
          </span>
          <button
            type="button"
            className={`${SECONDARY_BUTTON_CLASS} px-3 py-1 disabled:opacity-50`}
            onClick={() =>
              assessmentViewMode === "list"
                ? setAssessmentListPage((previous) => Math.min(currentAssessmentTotalPages, previous + 1))
                : setAssessmentGroupPage((previous) => Math.min(currentAssessmentTotalPages, previous + 1))
            }
            disabled={currentAssessmentPage >= currentAssessmentTotalPages}
          >
            Next
          </button>
        </div>
        </motion.section>
      ) : null}

      {deleteAssessmentPrompt ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4 backdrop-blur-[2px]">
          <div className="w-full max-w-md rounded-[28px] border border-rose-100 bg-white p-5 shadow-[0_24px_80px_-32px_rgba(15,23,42,0.45)]">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-rose-200 bg-rose-50 text-rose-700">
                <Trash size={18} weight="bold" />
              </div>
              <div className="min-w-0">
                <p className="text-lg font-semibold text-slate-900">Delete assessment</p>
                <p className="mt-1 text-sm text-slate-600">
                  This removes the submission, answers, uploaded evidence, and linked session data.
                </p>
                <p className="mt-3 rounded-2xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700">
                  {deleteAssessmentPrompt.summary}
                </p>
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                className={SECONDARY_BUTTON_CLASS}
                onClick={() => setDeleteAssessmentPrompt(null)}
                disabled={assessmentDeletingId === deleteAssessmentPrompt.submissionId}
              >
                Cancel
              </button>
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-full border border-rose-600 bg-rose-600 px-4 py-2 text-base font-semibold text-white shadow-[0_16px_32px_-18px_rgba(225,29,72,0.7)] transition hover:bg-rose-500 disabled:opacity-50"
                onClick={() => deleteAssessment(deleteAssessmentPrompt.submissionId)}
                disabled={assessmentDeletingId === deleteAssessmentPrompt.submissionId}
              >
                <Trash size={14} />
                {assessmentDeletingId === deleteAssessmentPrompt.submissionId ? "Deleting" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
      {incompleteActivityPrompt ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 backdrop-blur-[2px]">
          <div className="w-full max-w-xl rounded-[28px] border border-rose-100 bg-white p-5 shadow-[0_24px_80px_-32px_rgba(15,23,42,0.5)]">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-rose-200 bg-rose-50 text-rose-700">
                <Trash size={18} weight="bold" />
              </div>
              <div>
                <p className="text-lg font-semibold text-slate-900">Clear incomplete assessment activity?</p>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  This is permanent. Completed submissions, results, and their analytics will not be changed.
                </p>
              </div>
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["Incomplete sessions", incompleteActivityPrompt.incomplete_sessions],
                ["Unsubmitted drafts", incompleteActivityPrompt.unsubmitted_drafts],
                ["Uploaded documents", incompleteActivityPrompt.uploaded_documents],
                ["Processing jobs", incompleteActivityPrompt.processing_jobs],
              ].map(([label, value]) => (
                <div key={String(label)} className="rounded-2xl border border-slate-100 bg-slate-50 px-3 py-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
                  <p className="mt-1 text-xl font-semibold text-slate-900">{value}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-sm text-slate-500">
              Also removes {incompleteActivityPrompt.evidence_records} evidence artifact(s) and {incompleteActivityPrompt.stored_file_count} stored file(s) ({formatStoredBytes(incompleteActivityPrompt.stored_file_bytes)}).
            </p>
            {incompleteActivityPrompt.active_processing_jobs > 0 ? (
              <p className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm leading-6 text-amber-800">
                {incompleteActivityPrompt.active_processing_jobs} incomplete job(s) are still processing. Wait for them to finish, close this dialog, and check again.
              </p>
            ) : null}
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                className={SECONDARY_BUTTON_CLASS}
                onClick={() => setIncompleteActivityPrompt(null)}
                disabled={incompleteActivityDeleting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-full border border-rose-700 bg-rose-700 px-4 py-2 text-base font-semibold text-white transition hover:bg-rose-600 disabled:opacity-50"
                onClick={() => void resetIncompleteActivity()}
                disabled={
                  incompleteActivityDeleting
                  || incompleteActivityPrompt.active_processing_jobs > 0
                  || (incompleteActivityPrompt.incomplete_sessions === 0 && incompleteActivityPrompt.unsubmitted_drafts === 0)
                }
              >
                <Trash size={15} />
                {incompleteActivityDeleting ? "Clearing activity" : "Clear permanently"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {uiMode === "advanced" && rules && resolvedActiveSection === "rules" ? (
        <motion.section
          initial={{ opacity: 0, y: prefersReducedMotion ? 0 : 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={sectionTransition}
          className={`min-h-[520px] p-5 ${PANEL_CLASS}`}
        >
          <h2 className="text-xl font-semibold text-slate-800">Rules Configuration</h2>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={previewRules}
              className={GHOST_BUTTON_CLASS}
              type="button"
              disabled={previewLoading}
            >
              {previewLoading ? "Generating Preview..." : "Preview Rules"}
            </button>
          </div>
          {previewData ? (
            <div className="mt-3 rounded-2xl border border-emerald-100 bg-emerald-50/80 p-3">
              <p className="text-base font-semibold text-emerald-800">Preview Outcomes</p>
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                {previewData.sample_outcomes.map((item) => (
                  <div key={String(item.scenario)} className="rounded-2xl border border-emerald-100 bg-white p-2 text-base text-slate-700">
                    <p className="font-semibold text-slate-800">{String(item.scenario)}</p>
                    <p>Recommendation: {String(item.recommendation)}</p>
                    <p>Agile: {String(item.agile_score)} | Traditional: {String(item.traditional_score)}</p>
                    <p>Confidence: {String(item.confidence_level)}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            {(["construct_weights", "agile_baseline", "traditional_baseline"] as const).map((section) => {
              const sectionValues = ((((rules.payload ?? {}) as Record<string, unknown>)[section] ?? {}) as Record<string, number>);
              return (
                <div key={section} className="rounded-lg border border-slate-100 p-3">
                  <p className="text-base font-semibold capitalize text-slate-700">{section.replaceAll("_", " ")}</p>
                  <div className="mt-3 grid gap-2">
                    {Object.entries(sectionValues).map(([key, value]) => (
                      <label key={key} className="flex items-center justify-between gap-3 text-base text-slate-600">
                        <span>{key}</span>
                        <input
                          type="number"
                          step="0.1"
                          className="w-24 rounded-md border border-slate-300 px-2 py-1 text-right text-base"
                          value={value}
                          onChange={(event) => updateRuleNumber(section, key, event.target.value)}
                        />
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
            <div className="rounded-lg border border-slate-100 p-3">
              <p className="text-base font-semibold text-slate-700">Compatibility Calculation</p>
              <label className="mt-3 grid gap-1 text-base text-slate-600">
                <span>Normalization</span>
                <select
                  className="rounded-md border border-slate-300 px-2 py-1 text-base"
                  value={String((((rules.payload ?? {}) as Record<string, unknown>).compatibility_normalization ?? "legacy_fixed_15"))}
                  onChange={(event) => updateRuleSetting("compatibility_normalization", event.target.value)}
                >
                  <option value="weighted_range">Weighted range (recommended)</option>
                  <option value="legacy_fixed_15">Legacy fixed divisor</option>
                </select>
              </label>
              <label className="mt-3 flex items-center gap-2 text-base text-slate-600">
                <input
                  type="checkbox"
                  checked={Boolean((((rules.payload ?? {}) as Record<string, unknown>).strictness_override_enabled ?? true))}
                  onChange={(event) => updateRuleSetting("strictness_override_enabled", event.target.checked)}
                />
                Force Traditional above the strictness threshold
              </label>
              <label className="mt-3 flex items-center justify-between gap-3 text-base text-slate-600">
                <span>STRICTNESS threshold</span>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="5"
                  className="w-24 rounded-md border border-slate-300 px-2 py-1 text-right text-base"
                  disabled={!Boolean((((rules.payload ?? {}) as Record<string, unknown>).strictness_override_enabled ?? true))}
                  value={Number((((rules.payload ?? {}) as Record<string, unknown>).strictness_threshold ?? 0))}
                  onChange={(event) => updateRuleThreshold(event.target.value)}
                />
              </label>
            </div>
          </div>
          <div className="mt-4 rounded-lg border border-slate-100 p-3">
            <p className="text-base font-semibold text-slate-700">Driver Rules</p>
            <div className="mt-3 grid gap-3">
              {Object.entries((((rules.payload ?? {}) as Record<string, unknown>).driver_rules ?? {}) as Record<string, Record<string, unknown>>).map(
                ([ruleKey, rule]) => (
                  <div key={ruleKey} className="rounded-md border border-slate-100 p-3">
                    <p className="text-base font-semibold text-slate-600">{ruleKey}</p>
                    <div className="mt-2 grid gap-2 md:grid-cols-4">
                      <input
                        className="rounded-md border border-slate-300 px-2 py-1 text-base"
                        value={String(rule.label ?? "")}
                        onChange={(event) => updateDriverRule(ruleKey, "label", event.target.value)}
                        placeholder="Label"
                      />
                      <select
                        className="rounded-md border border-slate-300 px-2 py-1 text-base"
                        value={String(rule.construct ?? "FLEXIBILITY")}
                        onChange={(event) => updateDriverRule(ruleKey, "construct", event.target.value)}
                      >
                        <option value="FLEXIBILITY">FLEXIBILITY</option>
                        <option value="PERFORMANCE">PERFORMANCE</option>
                        <option value="STRICTNESS">STRICTNESS</option>
                      </select>
                      <select
                        className="rounded-md border border-slate-300 px-2 py-1 text-base"
                        value={String(rule.methodology ?? "Agile")}
                        onChange={(event) => updateDriverRule(ruleKey, "methodology", event.target.value)}
                      >
                        <option value="Agile">Agile</option>
                        <option value="Traditional">Traditional</option>
                      </select>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="5"
                        className="rounded-md border border-slate-300 px-2 py-1 text-base"
                        value={Number(rule.threshold ?? 0)}
                        onChange={(event) => updateDriverRule(ruleKey, "threshold", event.target.value)}
                        placeholder="Threshold"
                      />
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
          <div className="mt-4 rounded-lg border border-slate-100 p-3">
            <p className="text-base font-semibold text-slate-700">Risk Flag Rules</p>
            <div className="mt-3 grid gap-3">
              {Object.entries((((rules.payload ?? {}) as Record<string, unknown>).risk_flag_rules ?? {}) as Record<string, Record<string, unknown>>).map(
                ([ruleKey, rule]) => (
                  <div key={ruleKey} className="rounded-md border border-slate-100 p-3">
                    <p className="text-base font-semibold text-slate-600">{ruleKey}</p>
                    <div className="mt-2 grid gap-2 md:grid-cols-5">
                      <input
                        className="rounded-md border border-slate-300 px-2 py-1 text-base md:col-span-2"
                        value={String(rule.label ?? "")}
                        onChange={(event) => updateRiskRule(ruleKey, "label", event.target.value)}
                        placeholder="Label"
                      />
                      <select
                        className="rounded-md border border-slate-300 px-2 py-1 text-base"
                        value={String(rule.operator ?? "gte")}
                        onChange={(event) => updateRiskRule(ruleKey, "operator", event.target.value)}
                      >
                        <option value="gte">gte</option>
                        <option value="lte">lte</option>
                      </select>
                      <input
                        type="number"
                        step="0.1"
                        className="rounded-md border border-slate-300 px-2 py-1 text-base"
                        value={Number(rule.threshold ?? 0)}
                        onChange={(event) => updateRiskRule(ruleKey, "threshold", event.target.value)}
                        placeholder="Threshold"
                      />
                      {String(rule.metric ?? "").length > 0 ? (
                        <input
                          className="rounded-md border border-slate-300 px-2 py-1 text-base"
                          value={String(rule.metric ?? "")}
                          onChange={(event) => updateRiskRule(ruleKey, "metric", event.target.value)}
                          placeholder="Metric"
                        />
                      ) : (
                        <select
                          className="rounded-md border border-slate-300 px-2 py-1 text-base"
                          value={String(rule.construct ?? "FLEXIBILITY")}
                          onChange={(event) => updateRiskRule(ruleKey, "construct", event.target.value)}
                        >
                          <option value="FLEXIBILITY">FLEXIBILITY</option>
                          <option value="PERFORMANCE">PERFORMANCE</option>
                          <option value="STRICTNESS">STRICTNESS</option>
                        </select>
                      )}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {["dependent_variable_rules", "next_step_templates"].map((key) => (
              <details key={key} className="rounded-lg border border-slate-100 p-3">
                <summary className="cursor-pointer text-base font-semibold uppercase tracking-wide text-slate-500">
                  {key.replaceAll("_", " ")}
                </summary>
                <pre className="mt-2 max-h-44 overflow-auto whitespace-pre-wrap text-base text-slate-600">
                  {JSON.stringify(((rules.payload ?? {}) as Record<string, unknown>)[key] ?? {}, null, 2)}
                </pre>
              </details>
            ))}
          </div>
          <details className="mt-3 rounded-lg border border-slate-200 p-3">
            <summary className="cursor-pointer text-base font-semibold text-slate-700">
              Advanced JSON Editor
            </summary>
            <textarea
              id="rules-payload"
              name="rules_payload"
              className="mt-3 h-64 w-full rounded-md border border-slate-300 p-3 font-mono text-base"
              value={JSON.stringify(rules.payload ?? {}, null, 2)}
              onChange={(event) =>
                setRules((previous) => {
                  if (!previous) {
                    return previous;
                  }
                  try {
                    const nextPayload = JSON.parse(event.target.value) as Record<string, unknown>;
                    return { ...previous, payload: nextPayload };
                  } catch {
                    return previous;
                  }
                })
              }
            />
          </details>
          <input
            id="rules-change-note"
            name="rules_change_note"
            autoComplete="off"
            className="mt-3 w-full rounded-md border border-slate-300 p-2 text-base"
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
          <button onClick={saveRules} className={`mt-3 ${PRIMARY_BUTTON_CLASS}`} type="button">
            Save Rules
          </button>
          {ruleVersions.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {ruleVersions.map((version) => (
                <button
                  key={String(version.version)}
                  type="button"
                  onClick={() => activateRuleVersion(Number(version.version))}
                  className="rounded-full border border-slate-300 px-3 py-1 text-base font-medium text-slate-700"
                >
                  Activate v{String(version.version)}
                </button>
              ))}
            </div>
          ) : null}
        </motion.section>
      ) : null}

      {uiMode === "advanced" && activeQuestionnaire && resolvedActiveSection === "questionnaire" ? (
        <motion.section
          initial={{ opacity: 0, y: prefersReducedMotion ? 0 : 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={sectionTransition}
          className={`min-h-[520px] p-5 ${PANEL_CLASS}`}
        >
          <h2 className="text-xl font-semibold text-slate-800">Questionnaire Configuration</h2>
          <input
            id="questionnaire-title"
            name="questionnaire_title"
            autoComplete="off"
            className="mt-3 w-full rounded-md border border-slate-300 p-2 text-base"
            value={String(activeQuestionnaire.title ?? "Questionnaire")}
            onChange={(event) =>
              setActiveQuestionnaire((previous) =>
                previous ? { ...previous, title: event.target.value } : previous
              )
            }
          />
          <div className="mt-4 rounded-lg border border-slate-100 p-3">
            <div className="flex items-center justify-between">
              <p className="text-base font-semibold text-slate-700">Profile Questions</p>
              <button
                type="button"
                className="rounded-full border border-slate-300 px-3 py-1 text-base font-medium text-slate-700"
                onClick={addProfileQuestion}
              >
                Add Profile Question
              </button>
            </div>
            <div className="mt-3 space-y-3">
              {questionnairePayload.profile_questions.map((question, index) => (
                <div key={question.question_id} className="rounded-md border border-slate-100 p-3">
                  <div className="grid gap-2 md:grid-cols-4">
                    <input
                      className="rounded-md border border-slate-300 px-2 py-1 text-base"
                      value={question.question_id}
                      onChange={(event) => updateProfileQuestion(index, { question_id: event.target.value })}
                      placeholder="Question ID"
                    />
                    <select
                      className="rounded-md border border-slate-300 px-2 py-1 text-base"
                      value={question.kind}
                      onChange={(event) => {
                        const kind = event.target.value as "text" | "pill";
                        updateProfileQuestion(index, {
                          kind,
                          document_extraction: question.document_extraction
                            ? {
                                ...question.document_extraction,
                                answer_type: kind === "pill" ? "option" : "text",
                              }
                            : undefined,
                        });
                      }}
                    >
                      <option value="text">text</option>
                      <option value="pill">pill</option>
                    </select>
                    <input
                      className="rounded-md border border-slate-300 px-2 py-1 text-base"
                      value={question.profile_key}
                      onChange={(event) => updateProfileQuestion(index, { profile_key: event.target.value })}
                      placeholder="Profile key"
                    />
                    <input
                      className="rounded-md border border-slate-300 px-2 py-1 text-base"
                      value={question.prompt}
                      onChange={(event) => updateProfileQuestion(index, { prompt: event.target.value })}
                      placeholder="Prompt"
                    />
                  </div>
                  <div className="mt-2 grid gap-2 md:grid-cols-3">
                    <input
                      className="rounded-md border border-slate-300 px-2 py-1 text-base md:col-span-2"
                      value={question.placeholder ?? ""}
                      onChange={(event) => updateProfileQuestion(index, { placeholder: event.target.value })}
                      placeholder="Placeholder"
                    />
                    <input
                      className="rounded-md border border-slate-300 px-2 py-1 text-base"
                      value={(question.options ?? []).join(", ")}
                      onChange={(event) =>
                        updateProfileQuestion(index, {
                          options: event.target.value
                            ? event.target.value.split(",").map((value) => value.trim()).filter(Boolean)
                            : [],
                        })
                      }
                      placeholder="Options (comma separated)"
                    />
                  </div>
                  <div className="mt-3 rounded-xl border border-sky-100 bg-sky-50/60 p-3">
                    <label className="flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-700">
                      <input
                        type="checkbox"
                        checked={Boolean(question.document_extraction?.enabled)}
                        disabled
                        onChange={(event) =>
                          updateProfileQuestion(index, {
                            document_extraction: {
                              enabled: event.target.checked,
                              instruction:
                                question.document_extraction?.instruction
                                ?? "Extract a direct answer only when the document contains supporting evidence.",
                              answer_type: question.kind === "pill" ? "option" : "text",
                              rubric: question.document_extraction?.rubric ?? null,
                            },
                          })
                        }
                      />
                      Document extraction is configured through document-only evidence questions.
                    </label>
                    {question.document_extraction?.enabled ? (
                      <div className="mt-3 grid gap-2 md:grid-cols-2">
                        <input
                          className="rounded-md border border-sky-200 bg-white px-2 py-1 text-base"
                          value={question.document_extraction.instruction}
                          onChange={(event) =>
                            updateProfileQuestion(index, {
                              document_extraction: {
                                ...question.document_extraction!,
                                instruction: event.target.value,
                              },
                            })
                          }
                          placeholder="Extraction instruction"
                        />
                        <input
                          className="rounded-md border border-sky-200 bg-white px-2 py-1 text-base"
                          value={question.document_extraction.rubric ?? ""}
                          onChange={(event) =>
                            updateProfileQuestion(index, {
                              document_extraction: {
                                ...question.document_extraction!,
                                rubric: event.target.value || null,
                              },
                            })
                          }
                          placeholder="Optional evidence rubric"
                        />
                      </div>
                    ) : null}
                  </div>
                  <div className="mt-2 flex gap-2">
                    <button
                      type="button"
                      className="rounded-full border border-slate-300 px-3 py-1 text-base"
                      onClick={() =>
                        updateQuestionnairePayload({
                          ...questionnairePayload,
                          profile_questions: moveItem(questionnairePayload.profile_questions, index, -1),
                        })
                      }
                    >
                      Up
                    </button>
                    <button
                      type="button"
                      className="rounded-full border border-slate-300 px-3 py-1 text-base"
                      onClick={() =>
                        updateQuestionnairePayload({
                          ...questionnairePayload,
                          profile_questions: moveItem(questionnairePayload.profile_questions, index, 1),
                        })
                      }
                    >
                      Down
                    </button>
                    <button
                      type="button"
                      className="rounded-full border border-rose-300 px-3 py-1 text-base text-rose-700"
                      onClick={() =>
                        updateQuestionnairePayload({
                          ...questionnairePayload,
                          profile_questions: questionnairePayload.profile_questions.filter((_, itemIndex) => itemIndex !== index),
                        })
                      }
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 rounded-lg border border-slate-100 p-3">
            <div className="flex items-center justify-between">
              <p className="text-base font-semibold text-slate-700">Likert Questions</p>
              <button
                type="button"
                className="rounded-full border border-slate-300 px-3 py-1 text-base font-medium text-slate-700"
                onClick={addLikertQuestion}
              >
                Add Likert Question
              </button>
            </div>
            <div className="mt-3 space-y-3">
              {questionnairePayload.likert_questions.map((question, index) => (
                <div key={question.question_id} className="rounded-md border border-slate-100 p-3">
                  <div className="grid gap-2 md:grid-cols-3">
                    <input
                      className="rounded-md border border-slate-300 px-2 py-1 text-base"
                      value={question.question_id}
                      onChange={(event) => updateLikertQuestion(index, { question_id: event.target.value })}
                      placeholder="Question ID"
                    />
                    <select
                      className="rounded-md border border-slate-300 px-2 py-1 text-base"
                      value={question.construct}
                      onChange={(event) =>
                        updateLikertQuestion(index, {
                          construct: event.target.value as "FLEXIBILITY" | "PERFORMANCE" | "STRICTNESS",
                        })
                      }
                    >
                      <option value="FLEXIBILITY">FLEXIBILITY</option>
                      <option value="PERFORMANCE">PERFORMANCE</option>
                      <option value="STRICTNESS">STRICTNESS</option>
                    </select>
                    <input
                      className="rounded-md border border-slate-300 px-2 py-1 text-base"
                      value={question.prompt}
                      onChange={(event) => updateLikertQuestion(index, { prompt: event.target.value })}
                      placeholder="Prompt"
                    />
                  </div>
                  <div className="mt-3">
                    <p className="text-sm font-semibold text-slate-700">Answer anchors (1 to 5)</p>
                    <div className="mt-2 grid gap-2 md:grid-cols-5">
                      {(question.scale_labels ?? DEFAULT_LIKERT_SCALE_LABELS).map((label, labelIndex) => (
                        <label key={labelIndex} className="text-xs font-medium text-slate-500">
                          {labelIndex + 1}
                          <input
                            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-sm text-slate-700"
                            value={label}
                            onChange={(event) => updateLikertScaleLabel(index, labelIndex, event.target.value)}
                            placeholder={`Label ${labelIndex + 1}`}
                          />
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className="mt-3 rounded-xl border border-sky-100 bg-sky-50/60 p-3">
                    <label className="flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-700">
                      <input
                        type="checkbox"
                        checked={question.document_extraction?.enabled ?? false}
                        disabled
                        onChange={(event) =>
                          updateLikertQuestion(index, {
                            document_extraction: {
                              enabled: event.target.checked,
                              instruction:
                                question.document_extraction?.instruction
                                ?? "Use only direct document evidence. Return a score from 1 to 5 and cite the supporting text.",
                              answer_type: "likert",
                              rubric:
                                question.document_extraction?.rubric
                                ?? "1 means strongly disagrees, 3 means evidence is neutral or insufficient, and 5 means strongly agrees.",
                            },
                          })
                        }
                      />
                      User-reported ratings are not extracted from documents.
                    </label>
                    {(question.document_extraction?.enabled ?? false) ? (
                      <div className="mt-3 grid gap-2 md:grid-cols-2">
                        <input
                          className="rounded-md border border-sky-200 bg-white px-2 py-1 text-base"
                          value={
                            question.document_extraction?.instruction
                            ?? "Use only direct document evidence. Return a score from 1 to 5 and cite the supporting text."
                          }
                          onChange={(event) =>
                            updateLikertQuestion(index, {
                              document_extraction: {
                                enabled: true,
                                instruction: event.target.value,
                                answer_type: "likert",
                                rubric:
                                  question.document_extraction?.rubric
                                  ?? "1 means strongly disagrees, 3 means evidence is neutral or insufficient, and 5 means strongly agrees.",
                              },
                            })
                          }
                          placeholder="Extraction instruction"
                        />
                        <input
                          className="rounded-md border border-sky-200 bg-white px-2 py-1 text-base"
                          value={
                            question.document_extraction?.rubric
                            ?? "1 means strongly disagrees, 3 means evidence is neutral or insufficient, and 5 means strongly agrees."
                          }
                          onChange={(event) =>
                            updateLikertQuestion(index, {
                              document_extraction: {
                                enabled: true,
                                instruction:
                                  question.document_extraction?.instruction
                                  ?? "Use only direct document evidence. Return a score from 1 to 5 and cite the supporting text.",
                                answer_type: "likert",
                                rubric: event.target.value || null,
                              },
                            })
                          }
                          placeholder="Scoring rubric"
                        />
                      </div>
                    ) : null}
                  </div>
                  <div className="mt-2 flex gap-2">
                    <button
                      type="button"
                      className="rounded-full border border-slate-300 px-3 py-1 text-base"
                      onClick={() =>
                        updateQuestionnairePayload({
                          ...questionnairePayload,
                          likert_questions: moveItem(questionnairePayload.likert_questions, index, -1),
                        })
                      }
                    >
                      Up
                    </button>
                    <button
                      type="button"
                      className="rounded-full border border-slate-300 px-3 py-1 text-base"
                      onClick={() =>
                        updateQuestionnairePayload({
                          ...questionnairePayload,
                          likert_questions: moveItem(questionnairePayload.likert_questions, index, 1),
                        })
                      }
                    >
                      Down
                    </button>
                    <button
                      type="button"
                      className="rounded-full border border-rose-300 px-3 py-1 text-base text-rose-700"
                      onClick={() =>
                        updateQuestionnairePayload({
                          ...questionnairePayload,
                          likert_questions: questionnairePayload.likert_questions.filter((_, itemIndex) => itemIndex !== index),
                        })
                      }
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50/40 p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-base font-semibold text-slate-700">Document-Only Evidence Questions</p>
                <p className="mt-1 text-sm text-slate-600">These cited, optional answers can contribute up to 25% of each construct score. They are not user questionnaire questions.</p>
              </div>
              <button type="button" className="rounded-full border border-blue-300 bg-white px-3 py-1 text-base font-medium text-blue-800" onClick={addDocumentQuestion}>
                Add Document Question
              </button>
            </div>
            <div className="mt-3 space-y-3">
              {questionnairePayload.document_questions.map((question, index) => (
                <div key={question.question_id} className="rounded-md border border-blue-100 bg-white p-3">
                  <div className="grid gap-2 md:grid-cols-[120px_170px_100px_minmax(0,1fr)]">
                    <input className="rounded-md border border-slate-300 px-2 py-1 text-base" value={question.question_id} onChange={(event) => updateDocumentQuestion(index, { question_id: event.target.value })} placeholder="Question ID" />
                    <select className="rounded-md border border-slate-300 px-2 py-1 text-base" value={question.construct} onChange={(event) => updateDocumentQuestion(index, { construct: event.target.value as DocumentQuestion["construct"] })}>
                      <option value="FLEXIBILITY">FLEXIBILITY</option>
                      <option value="PERFORMANCE">PERFORMANCE</option>
                      <option value="STRICTNESS">STRICTNESS</option>
                    </select>
                    <input className="rounded-md border border-slate-300 px-2 py-1 text-base" type="number" min="0.1" max="3" step="0.1" value={question.weight} onChange={(event) => updateDocumentQuestion(index, { weight: Number(event.target.value) || 1 })} aria-label={`${question.question_id} weight`} />
                    <input className="rounded-md border border-slate-300 px-2 py-1 text-base" value={question.prompt} onChange={(event) => updateDocumentQuestion(index, { prompt: event.target.value })} placeholder="Document-only prompt" />
                  </div>
                  <div className="mt-2 flex gap-2">
                    <button type="button" className="rounded-full border border-slate-300 px-3 py-1 text-base" onClick={() => updateQuestionnairePayload({ ...questionnairePayload, document_questions: moveItem(questionnairePayload.document_questions, index, -1) })}>Up</button>
                    <button type="button" className="rounded-full border border-slate-300 px-3 py-1 text-base" onClick={() => updateQuestionnairePayload({ ...questionnairePayload, document_questions: moveItem(questionnairePayload.document_questions, index, 1) })}>Down</button>
                    <button type="button" className="rounded-full border border-rose-300 px-3 py-1 text-base text-rose-700" onClick={() => updateQuestionnairePayload({ ...questionnairePayload, document_questions: questionnairePayload.document_questions.filter((_, itemIndex) => itemIndex !== index) })}>Remove</button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <details className="mt-3 rounded-lg border border-slate-200 p-3">
            <summary className="cursor-pointer text-base font-semibold text-slate-700">
              Advanced JSON Editor
            </summary>
            <textarea
              id="questionnaire-payload"
              name="questionnaire_payload"
              className="mt-3 h-72 w-full rounded-md border border-slate-300 p-3 font-mono text-base"
              value={JSON.stringify(activeQuestionnaire.payload ?? {}, null, 2)}
              onChange={(event) =>
                setActiveQuestionnaire((previous) => {
                  if (!previous) {
                    return previous;
                  }
                  try {
                    return { ...previous, payload: JSON.parse(event.target.value) as Record<string, unknown> };
                  } catch {
                    return previous;
                  }
                })
              }
            />
          </details>
          <input
            id="questionnaire-change-note"
            name="questionnaire_change_note"
            autoComplete="off"
            className="mt-3 w-full rounded-md border border-slate-300 p-2 text-base"
            value={questionnaireNote}
            onChange={(event) => setQuestionnaireNote(event.target.value)}
          />
          <button
            onClick={saveQuestionnaire}
            className={`mt-3 ${PRIMARY_BUTTON_CLASS}`}
            type="button"
          >
            Save Questionnaire Version
          </button>
          {questionnaires.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {questionnaires.map((version) => (
                <button
                  key={String(version.version)}
                  type="button"
                  onClick={() => activateQuestionnaireVersion(Number(version.version))}
                  className="rounded-full border border-slate-300 px-3 py-1 text-base font-medium text-slate-700"
                >
                  Activate Q v{String(version.version)}
                </button>
              ))}
            </div>
          ) : null}
        </motion.section>
      ) : null}

      {uiMode === "advanced" && canManageUsers && resolvedActiveSection === "users" ? (
        <motion.section
          initial={{ opacity: 0, y: prefersReducedMotion ? 0 : 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={sectionTransition}
          className={`min-h-[520px] p-5 ${PANEL_CLASS}`}
        >
          <h2 className="text-xl font-semibold text-slate-800">Admin Users</h2>
        <form
          className="mt-3 grid gap-3 md:grid-cols-4"
          onSubmit={(event) => {
            event.preventDefault();
            void createAdminUser();
          }}
        >
          <input
            id="new-admin-email"
            name="new_admin_email"
            autoComplete="username"
            className="rounded-md border border-slate-300 p-2 text-base"
            placeholder="Email"
            value={newUserEmail}
            onChange={(event) => {
              setNewUserEmail(event.target.value);
              setNewUserFormError(null);
            }}
          />
          <input
            id="new-admin-password"
            name="new_admin_password"
            autoComplete="new-password"
            className="rounded-md border border-slate-300 p-2 text-base"
            placeholder="Password"
            type="password"
            value={newUserPassword}
            onChange={(event) => {
              setNewUserPassword(event.target.value);
              setNewUserFormError(null);
            }}
          />
          <select
            id="new-admin-role"
            name="new_admin_role"
            className="rounded-md border border-slate-300 p-2 text-base"
            value={newUserRole}
            onChange={(event) => setNewUserRole(event.target.value)}
          >
            <option value="analyst">analyst</option>
            <option value="config_editor">config_editor</option>
            <option value="super_admin">super_admin</option>
          </select>
          <button
            type="submit"
            className={`${PRIMARY_BUTTON_CLASS} disabled:cursor-not-allowed disabled:opacity-60`}
            disabled={creatingAdminUser}
          >
            {creatingAdminUser ? "Creating..." : "Create User"}
          </button>
        </form>
        {newUserFormError ? <p className="mt-2 text-sm font-medium text-rose-700" role="alert">{newUserFormError}</p> : null}

        <div className="mt-4 overflow-auto">
          <table className="min-w-full text-left text-base">
            <thead>
              <tr className="text-slate-500">
                <th className="py-2">Email</th>
                <th>Role</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {adminUsers.map((user) => (
                <tr key={user.id} className="border-t border-slate-100">
                  <td className="py-2">{user.email}</td>
                  <td>
                    <select
                      id={`admin-role-${user.id}`}
                      name={`admin_role_${user.id}`}
                      className="rounded-md border border-slate-300 p-1 text-base"
                      value={user.role}
                      onChange={(event) =>
                        setAdminUsers((prev) =>
                          prev.map((item) =>
                            item.id === user.id ? { ...item, role: event.target.value } : item
                          )
                        )
                      }
                    >
                      <option value="analyst">analyst</option>
                      <option value="config_editor">config_editor</option>
                      <option value="super_admin">super_admin</option>
                    </select>
                  </td>
                  <td>
                    <input
                      id={`admin-active-${user.id}`}
                      name={`admin_active_${user.id}`}
                      type="checkbox"
                      checked={user.is_active}
                      onChange={(event) =>
                        setAdminUsers((prev) =>
                          prev.map((item) =>
                            item.id === user.id ? { ...item, is_active: event.target.checked } : item
                          )
                        )
                      }
                    />
                  </td>
                  <td>
                    <button
                      type="button"
                      className="rounded-full border border-slate-300 px-3 py-1 text-base font-medium text-slate-700"
                      onClick={() => updateAdminUser(user, user.role, user.is_active)}
                    >
                      Save
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        </motion.section>
      ) : null}
      </div>
      </div>
    </AdminWorkspaceShell>
  );
}
