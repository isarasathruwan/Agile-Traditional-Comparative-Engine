"use client";

import { ArrowLeft, ArrowClockwise, FileText, ShieldCheck, Trash } from "@phosphor-icons/react";
import { useState } from "react";
import type { AssessmentDetail } from "@/lib/adminAssessment";

type Tab = "decision" | "answers" | "evidence" | "advisor";

type Props = {
  assessment: AssessmentDetail;
  canWrite: boolean;
  deleting: boolean;
  retrying: boolean;
  onBack: () => void;
  onDelete: () => Promise<void>;
  onRetryDocuments: () => Promise<void>;
  onRetryAdvisor: () => Promise<void>;
  onOpenDocument: (path: string, mode: "preview" | "download", filename?: string) => Promise<void>;
};

const label = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`border border-slate-200 bg-white ${className}`}>{children}</section>;
}

export default function AdminAssessmentWorkspace({
  assessment,
  canWrite,
  deleting,
  retrying,
  onBack,
  onDelete,
  onRetryDocuments,
  onRetryAdvisor,
  onOpenDocument,
}: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("decision");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const advisor = assessment.traditional_advisor;
  const scoreGap = Math.abs(assessment.agile_score - assessment.traditional_score).toFixed(1);
  const projectName = assessment.profile_answers.find((item) => item.profile_key === "projectName")?.answer;
  const companyName = assessment.profile_answers.find((item) => item.profile_key === "company")?.answer;
  const tabs: Array<{ key: Tab; label: string }> = [
    { key: "decision", label: "Decision" },
    { key: "answers", label: "Answers" },
    { key: "evidence", label: "Evidence" },
    { key: "advisor", label: "AI Advisor" },
  ];

  return (
    <div className="min-h-full bg-[#f6f8fc] text-slate-900">
      <div>
        <header className="flex min-h-16 items-center justify-between gap-4 border-b border-slate-200 bg-white px-4 py-3 sm:px-6 lg:px-8 xl:px-12">
          <div className="flex min-w-0 items-center gap-3">
            <button type="button" onClick={onBack} className="inline-flex h-9 w-9 shrink-0 items-center justify-center border border-slate-300 bg-white text-slate-600 hover:border-blue-300 hover:text-blue-700" aria-label="Back to assessments" title="Back to assessments">
              <ArrowLeft size={18} />
            </button>
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Assessment review</p>
              <h1 className="truncate text-lg font-semibold text-slate-950 sm:text-xl">{projectName || `Assessment #${assessment.submission_id}`}</h1>
              <p className="truncate text-xs text-slate-500">#{assessment.submission_id} · {companyName || "Assessment participant"} · {new Date(assessment.created_at).toLocaleString()}</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <span className={`hidden border px-3 py-1.5 text-sm font-semibold sm:inline-flex ${assessment.recommendation === "Traditional" ? "border-blue-200 bg-blue-50 text-blue-800" : "border-cyan-200 bg-cyan-50 text-cyan-800"}`}>
              {assessment.recommendation}
            </span>
            {canWrite ? <button type="button" onClick={() => setConfirmDelete(true)} disabled={deleting} className="inline-flex h-9 w-9 items-center justify-center border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 disabled:opacity-50" aria-label="Delete assessment" title="Delete assessment">
              <Trash size={17} />
            </button> : null}
          </div>
        </header>

        <nav className="border-b border-slate-200 bg-[#f9fafc] px-4 sm:px-6 lg:px-8 xl:px-12" aria-label="Assessment detail sections">
          <div className="flex min-w-max gap-1 overflow-x-auto" role="tablist">
            {tabs.map((tab) => (
              <button key={tab.key} id={`assessment-${tab.key}-tab`} type="button" role="tab" aria-selected={activeTab === tab.key} onClick={() => setActiveTab(tab.key)} className={`border-b-2 px-4 py-3 text-sm font-semibold transition-colors ${activeTab === tab.key ? "border-blue-700 text-blue-700" : "border-transparent text-slate-500 hover:text-slate-900"}`}>
                {tab.label}
              </button>
            ))}
          </div>
        </nav>

        <div className="p-4 sm:p-6 lg:p-8 xl:px-12">
          <div className="w-full">
            {activeTab === "decision" ? (
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(300px,0.65fr)]">
                <Panel className="p-5 sm:p-7">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Recommended direction</p>
                  <h2 className="mt-2 text-3xl font-semibold text-slate-950">Use {assessment.recommendation}</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{String((assessment.decision_report as { methodology_fit_summary?: string }).methodology_fit_summary ?? "Assessment scores and project signals support this methodology direction.")}</p>
                  <div className="mt-7 grid border-y border-slate-200 sm:grid-cols-3">
                    <Score label="Traditional" value={assessment.traditional_score} selected={assessment.recommendation === "Traditional"} />
                    <Score label="Agile" value={assessment.agile_score} selected={assessment.recommendation === "Agile"} />
                    <div className="border-t border-slate-200 px-0 py-4 sm:border-l sm:border-t-0 sm:px-5"><p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Decision gap</p><p className="mt-2 text-2xl font-semibold text-slate-950">{scoreGap}</p><p className="mt-1 text-xs text-slate-500">points between methods</p></div>
                  </div>
                  <div className="mt-6 grid gap-px border border-slate-200 bg-slate-200 sm:grid-cols-3">
                    {Object.entries(assessment.construct_scores).map(([key, value]) => <div key={key} className="bg-white px-4 py-4"><p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">{label(key)}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value.toFixed(2)}</p></div>)}
                  </div>
                </Panel>
                <Panel className="p-5 sm:p-6"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Project snapshot</p><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{assessment.profile_answers.slice(3).map((item) => <div key={item.question_id} className="py-3"><p className="text-xs text-slate-500">{item.prompt}</p><p className="mt-1 text-sm font-semibold text-slate-800">{item.answer || "Not provided"}</p></div>)}</div></Panel>
              </div>
            ) : null}

            {activeTab === "answers" ? (
              <div className="grid gap-5 xl:grid-cols-2">
                <Panel className="p-5 sm:p-6"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Project context</p><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{assessment.profile_answers.map((item) => <div key={item.question_id} className="grid gap-2 py-3 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.85fr)]"><p className="text-sm text-slate-600">{item.question_id} · {item.prompt}</p><p className="text-sm font-semibold text-slate-900">{item.answer || "Not provided"}</p></div>)}</div></Panel>
                <Panel className="p-5 sm:p-6"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Method signals</p><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{assessment.likert_answers.map((item) => <div key={item.question_id} className="grid gap-3 py-3 sm:grid-cols-[minmax(0,1fr)_72px]"><div><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{item.question_id} · {item.construct}</p><p className="mt-1 text-sm text-slate-700">{item.prompt}</p></div><p className="self-start border border-slate-200 bg-slate-50 py-2 text-center text-sm font-semibold text-slate-900">{item.answer}/5</p></div>)}</div></Panel>
              </div>
            ) : null}

            {activeTab === "evidence" ? (
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
                <Panel className="p-5 sm:p-6"><div className="flex items-start justify-between gap-3"><div><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Uploaded documents</p><p className="mt-2 text-sm text-slate-600">{assessment.documents.length} file(s) attached to this assessment.</p></div>{canWrite && assessment.documents.some((document) => ["failed", "unsupported"].includes(document.status)) ? <button type="button" onClick={() => void onRetryDocuments()} disabled={retrying} className="inline-flex items-center gap-2 border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"><ArrowClockwise size={16} />Retry failed files</button> : null}</div><div className="mt-5 divide-y divide-slate-200 border-y border-slate-200">{assessment.documents.length ? assessment.documents.map((document) => <div key={document.id} className="flex flex-wrap items-center justify-between gap-3 py-4"><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-900">{document.filename}</p><p className="mt-1 text-xs text-slate-500">{document.status} · {(document.file_size / 1024).toFixed(1)} KB</p></div><div className="flex gap-2"><button type="button" onClick={() => void onOpenDocument(document.preview_url, "preview", document.filename)} className="border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700">Preview</button><button type="button" onClick={() => void onOpenDocument(document.download_url, "download", document.filename)} className="border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700">Download</button></div></div>) : <p className="py-6 text-sm text-slate-500">No uploaded documents were attached to this assessment.</p>}</div></Panel>
                <Panel className="p-5 sm:p-6"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Processing trace</p><div className="mt-4 space-y-3">{assessment.ai_demo_trace.length ? assessment.ai_demo_trace.map((step, index) => <div key={`${step.stage}-${index}`} className="border-l-2 border-blue-600 pl-3"><div className="flex justify-between gap-3"><p className="text-sm font-semibold text-slate-800">{step.label}</p><span className="text-xs text-slate-500">{step.duration_ms} ms</span></div><p className="mt-1 text-sm leading-5 text-slate-600">{step.detail}</p></div>) : <p className="text-sm text-slate-500">No processing trace was stored.</p>}</div><div className="mt-6 border-t border-slate-200 pt-5"><p className="text-sm font-semibold text-slate-800">Candidate signals</p><div className="mt-3 space-y-2">{assessment.ai_demo_summary.candidate_signals.length ? assessment.ai_demo_summary.candidate_signals.map((signal) => <div key={signal.key} className="border border-slate-200 bg-slate-50 px-3 py-2"><p className="text-sm font-semibold text-slate-800">{signal.label}</p><p className="mt-1 text-xs text-slate-500">{signal.source} · {signal.confidence}</p></div>) : <p className="text-sm text-slate-500">No candidate signals were recorded.</p>}</div></div></Panel>
              </div>
            ) : null}

            {activeTab === "advisor" ? <AdvisorPanel advisor={advisor} retrying={retrying} canRetry={canWrite} onRetry={() => void onRetryAdvisor()} /> : null}
          </div>
        </div>
      </div>

      {confirmDelete ? <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4"><Panel className="w-full max-w-md p-5 shadow-2xl"><p className="text-lg font-semibold text-slate-950">Delete assessment?</p><p className="mt-2 text-sm leading-6 text-slate-600">This removes the submission, answers, documents, and linked assessment data.</p><div className="mt-5 flex justify-end gap-2"><button type="button" onClick={() => setConfirmDelete(false)} disabled={deleting} className="border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700">Cancel</button><button type="button" onClick={() => void onDelete()} disabled={deleting} className="inline-flex items-center gap-2 border border-rose-700 bg-rose-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"><Trash size={16} />{deleting ? "Deleting" : "Delete"}</button></div></Panel></div> : null}
    </div>
  );
}

function Score({ label, value, selected }: { label: string; value: number; selected: boolean }) {
  return <div className={`px-0 py-4 sm:px-5 ${selected ? "bg-blue-50" : ""}`}><p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value.toFixed(2)}</p><div className="mt-3 h-1.5 bg-slate-200"><div className={selected ? "h-full bg-blue-700" : "h-full bg-slate-500"} style={{ width: `${Math.min(100, value)}%` }} /></div></div>;
}

function AdvisorPanel({ advisor, retrying, canRetry, onRetry }: { advisor: AssessmentDetail["traditional_advisor"]; retrying: boolean; canRetry: boolean; onRetry: () => void }) {
  if (!advisor || advisor.status === "not_applicable") return <Panel className="p-6"><ShieldCheck size={24} className="text-slate-500" /><h2 className="mt-3 text-xl font-semibold text-slate-950">No Traditional sub-methodology advice</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">This assessment recommended Agile, so a Traditional delivery-method recommendation was not generated.</p></Panel>;
  if (advisor.status !== "ready" || !advisor.advisor) return <Panel className="p-6"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Traditional methodology advisor</p><h2 className="mt-3 text-xl font-semibold text-slate-950">{advisor.status === "failed" ? "Advice is unavailable" : "Advice is processing"}</h2><p className="mt-2 text-sm text-slate-600">{advisor.error_message ?? "The advisor is evaluating assessment signals and evidence."}</p>{canRetry && advisor.status === "failed" && advisor.retry_allowed ? <button type="button" onClick={onRetry} disabled={retrying} className="mt-5 inline-flex items-center gap-2 border border-blue-300 bg-white px-3 py-2 text-sm font-semibold text-blue-800 disabled:opacity-50"><ArrowClockwise size={16} />{retrying ? "Queueing retry" : "Retry advice"}</button> : null}</Panel>;
  const data = advisor.advisor;
  return <div className="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]"><Panel className="p-5 sm:p-7"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Traditional methodology advisor</p><h2 className="mt-2 text-3xl font-semibold text-slate-950">{data.recommended_method}</h2><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">{data.recommendation_summary}</p><h3 className="mt-6 text-sm font-semibold text-slate-900">Why this method fits</h3><p className="mt-2 text-sm leading-6 text-slate-600">{data.rationale}</p><h3 className="mt-6 text-sm font-semibold text-slate-900">Alternatives considered</h3><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{data.alternatives.map((item) => <div key={item.method} className="py-3"><p className="text-sm font-semibold text-slate-800">{item.method}</p><p className="mt-1 text-sm text-slate-600">{item.reason}</p></div>)}</div></Panel><Panel className="p-5 sm:p-6"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Three-phase rollout</p><ol className="mt-4 space-y-4">{data.rollout.map((phase, index) => <li key={`${phase.phase}-${index}`} className="border-l-2 border-blue-600 pl-3"><p className="text-sm font-semibold text-slate-900">{phase.phase}</p><p className="mt-1 text-sm text-slate-700">{phase.objective}</p><p className="mt-2 text-sm text-slate-600">{phase.actions.join("; ")}</p>{phase.control_artifacts.length ? <p className="mt-2 text-xs text-slate-500">Controls: {phase.control_artifacts.join(", ")}</p> : null}</li>)}</ol><h3 className="mt-6 text-sm font-semibold text-slate-900">Tradeoffs</h3><ul className="mt-3 space-y-2 text-sm text-slate-600">{data.tradeoffs.map((item) => <li key={item}>{item}</li>)}</ul><h3 className="mt-6 text-sm font-semibold text-slate-900">Evidence and limits</h3><div className="mt-3 space-y-3">{data.evidence.map((item) => <div key={item.claim}><p className="text-sm text-slate-700">{item.claim}</p>{item.citations.map((citation, index) => <p key={`${citation.filename}-${index}`} className="mt-1 text-xs text-slate-500"><FileText size={13} className="mr-1 inline" />{citation.filename}{citation.page_number ? ` · page ${citation.page_number}` : ""}</p>)}</div>)}{data.limitations.map((item) => <p key={item} className="text-xs text-slate-500">{item}</p>)}</div></Panel></div>;
}
