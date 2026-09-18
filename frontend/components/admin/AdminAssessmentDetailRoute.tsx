"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AdminAssessmentWorkspace from "@/components/admin/AdminAssessmentWorkspace";
import AdminWorkspaceShell, { type AdminWorkspaceSection } from "@/components/admin/AdminWorkspaceShell";
import type { AssessmentDetail } from "@/lib/adminAssessment";
import { API_BASE_URL } from "@/lib/api";
import { adminDelete, adminGet, adminOpenFile, adminPost, isAdminUnauthenticated } from "@/lib/adminApi";
import { ADMIN_SECTION_LABELS } from "@/lib/pageMeta";

type Props = {
  submissionId: number;
};

const ADMIN_FORCE_LOGIN_KEY = "admin_force_login";
const ADMIN_SECTIONS: AdminWorkspaceSection[] = [
  { key: "overview", label: ADMIN_SECTION_LABELS.overview, advancedOnly: false },
  { key: "assessments", label: ADMIN_SECTION_LABELS.assessments, advancedOnly: false },
  { key: "rules", label: ADMIN_SECTION_LABELS.rules, advancedOnly: true },
  { key: "questionnaire", label: ADMIN_SECTION_LABELS.questionnaire, advancedOnly: true },
  { key: "users", label: ADMIN_SECTION_LABELS.users, advancedOnly: true },
];
const SECTION_ACCESS = {
  overview: "analytics:read",
  assessments: "assessments:read",
  rules: "rules:read",
  questionnaire: "questionnaire:read",
  users: "admin_users:read",
} as const;

function LoadingState({ submissionId, message = "Loading the assessment record and evidence." }: { submissionId: number; message?: string }) {
  return (
    <main className="grid h-[100dvh] place-items-center bg-[#f6f8fc] px-6 text-slate-900">
      <section className="w-full max-w-md border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-blue-200 border-t-blue-700" />
          <div>
            <p className="text-sm font-semibold">Opening assessment #{submissionId}</p>
            <p className="mt-1 text-sm text-slate-600">{message}</p>
          </div>
        </div>
      </section>
    </main>
  );
}

export default function AdminAssessmentDetailRoute({ submissionId }: Props) {
  const router = useRouter();
  const tokenRef = useRef<string | null>(null);
  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [canWrite, setCanWrite] = useState(false);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [uiMode, setUiMode] = useState<"guided" | "advanced">("guided");

  const returnToLogin = useCallback(() => {
    window.localStorage.removeItem("admin_token");
    window.sessionStorage.setItem(ADMIN_FORCE_LOGIN_KEY, "1");
    router.replace("/admin");
  }, [router]);

  const handleRequestError = useCallback((requestError: unknown, fallback: string) => {
    if (
      isAdminUnauthenticated(requestError)
    ) {
      returnToLogin();
      return;
    }
    setError(requestError instanceof Error ? requestError.message : fallback);
  }, [returnToLogin]);

  const loadAssessment = useCallback(async (accessToken: string, showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);
    try {
      const detail = await adminGet(`/api/v1/admin/assessments/${submissionId}`, accessToken) as AssessmentDetail;
      setAssessment(detail);
    } catch (requestError: unknown) {
      handleRequestError(requestError, "Assessment detail failed to load.");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [handleRequestError, submissionId]);

  useEffect(() => {
    const existingToken = window.localStorage.getItem("admin_token");
    if (!existingToken || window.sessionStorage.getItem(ADMIN_FORCE_LOGIN_KEY) === "1") {
      returnToLogin();
      return;
    }
    tokenRef.current = existingToken;
    const loadAuthorizedAssessment = async () => {
      try {
        const identity = await adminGet("/api/v1/admin/me", existingToken) as { permissions: string[] };
        if (!identity.permissions.includes("assessments:read")) {
          setError("You do not have permission to view assessment records.");
          setLoading(false);
          return;
        }
        setPermissions(identity.permissions);
        setCanWrite(identity.permissions.includes("assessments:write"));
        await loadAssessment(existingToken);
      } catch (requestError: unknown) {
        handleRequestError(requestError, "Unable to load your assessment access.");
        setLoading(false);
      }
    };
    void loadAuthorizedAssessment();
  }, [handleRequestError, loadAssessment, returnToLogin]);

  useEffect(() => {
    document.title = `Assessment #${submissionId} | MethodAlign IS`;
  }, [submissionId]);

  const deleteAssessment = async () => {
    const token = tokenRef.current;
    if (!token || deleting) return;
    setDeleting(true);
    try {
      await adminDelete(`/api/v1/admin/assessments/${submissionId}`, token);
      router.replace("/admin?section=assessments");
    } catch (requestError: unknown) {
      handleRequestError(requestError, "Assessment delete failed.");
      setDeleting(false);
    }
  };

  const retryDocumentProcessing = async () => {
    const token = tokenRef.current;
    if (!token || retrying) return;
    setRetrying(true);
    try {
      await adminPost(`/api/v1/admin/assessments/${submissionId}/document-processing/retry`, token, {});
      await loadAssessment(token, false);
    } catch (requestError: unknown) {
      handleRequestError(requestError, "Document processing retry failed.");
    } finally {
      setRetrying(false);
    }
  };

  const retryTraditionalAdvisor = async () => {
    const token = tokenRef.current;
    if (!token || retrying) return;
    setRetrying(true);
    try {
      await adminPost(`/api/v1/admin/assessments/${submissionId}/traditional-advisor/retry`, token, {});
      await loadAssessment(token, false);
    } catch (requestError: unknown) {
      handleRequestError(requestError, "Traditional delivery advice retry failed.");
    } finally {
      setRetrying(false);
    }
  };

  const openDocument = async (path: string, mode: "preview" | "download", filename?: string) => {
    const token = tokenRef.current;
    if (!token) return;
    setError(null);
    try {
      await adminOpenFile(path, token, mode, filename);
    } catch (requestError: unknown) {
      handleRequestError(requestError, "Unable to open document.");
    }
  };

  const downloadCsv = async () => {
    const token = tokenRef.current;
    if (!token) return;
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/export.csv`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error("CSV export failed.");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "assessments.csv";
      anchor.click();
      window.URL.revokeObjectURL(url);
    } catch (requestError: unknown) {
      handleRequestError(requestError, "CSV export failed.");
    }
  };

  if (loading) {
    return <LoadingState submissionId={submissionId} />;
  }

  if (!assessment) {
    return (
      <main className="grid h-[100dvh] place-items-center bg-[#f6f8fc] px-6 text-slate-900">
        <section className="w-full max-w-md border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold">Assessment could not be opened</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">{error ?? "The requested assessment is unavailable."}</p>
          <button type="button" onClick={() => router.replace("/admin?section=assessments")} className="mt-5 border border-blue-300 bg-white px-4 py-2 text-sm font-semibold text-blue-800">Back to assessments</button>
        </section>
      </main>
    );
  }

  const visibleSections = ADMIN_SECTIONS.filter((section) => permissions.includes(SECTION_ACCESS[section.key]));

  return (
    <AdminWorkspaceShell
      activeSection="assessments"
      sections={visibleSections}
      uiMode={uiMode}
      onNavigate={(section) => router.push(`/admin?section=${section}`)}
      onToggleUiMode={() => setUiMode((current) => (current === "guided" ? "advanced" : "guided"))}
      canExport={permissions.includes("assessments:export")}
      onExport={downloadCsv}
      onSignOut={() => returnToLogin()}
    >
      {error ? <div className="fixed left-4 right-4 top-4 z-40 mx-auto max-w-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}
      <AdminAssessmentWorkspace
        assessment={assessment}
        canWrite={canWrite}
        deleting={deleting}
        retrying={retrying}
        onBack={() => router.push("/admin?section=assessments")}
        onDelete={deleteAssessment}
        onRetryDocuments={retryDocumentProcessing}
        onRetryAdvisor={retryTraditionalAdvisor}
        onOpenDocument={openDocument}
      />
    </AdminWorkspaceShell>
  );
}
