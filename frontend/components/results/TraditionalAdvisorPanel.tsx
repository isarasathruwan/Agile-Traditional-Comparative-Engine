"use client";

import { ArrowClockwise, FileText, Strategy } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import {
  getTraditionalAdvisor,
  retryTraditionalAdvisor,
  type TraditionalAdvisorData,
} from "@/lib/api";

export default function TraditionalAdvisorPanel({ submissionId, initial }: { submissionId: number; initial?: TraditionalAdvisorData | null }) {
  const [advisor, setAdvisor] = useState<TraditionalAdvisorData | null>(initial ?? null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (advisor?.status !== "queued" && advisor?.status !== "running") return;
    let active = true;
    const poll = async () => {
      try {
        const value = await getTraditionalAdvisor(submissionId);
        if (active) setAdvisor(value);
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "Unable to load delivery advice.");
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 2200);
    return () => { active = false; window.clearInterval(timer); };
  }, [advisor?.status, submissionId]);

  const retry = async () => {
    setRetrying(true); setError(null);
    try { setAdvisor(await retryTraditionalAdvisor(submissionId)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to retry delivery advice."); }
    finally { setRetrying(false); }
  };

  if (!advisor || advisor.status === "queued" || advisor.status === "running") {
    return <section className="border border-blue-200 bg-blue-50 px-5 py-5"><div className="flex items-center gap-3"><span className="h-5 w-5 animate-spin rounded-full border-2 border-blue-200 border-t-blue-700" /><div><p className="text-sm font-semibold text-slate-900">Preparing Traditional delivery advice</p><p className="mt-1 text-sm text-slate-600">Reviewing project signals and the submitted evidence for a suitable predictive method.</p></div></div></section>;
  }
  if (advisor.status === "failed") {
    return <section className="border border-amber-200 bg-amber-50 px-5 py-5"><p className="font-semibold text-slate-900">Delivery advice is unavailable</p><p className="mt-1 text-sm text-slate-600">{advisor.error_message ?? error ?? "The assessment result is still available."}</p>{advisor.retry_allowed ? <button type="button" onClick={retry} disabled={retrying} className="mt-4 inline-flex items-center gap-2 border border-amber-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800 disabled:opacity-60"><ArrowClockwise size={16} />{retrying ? "Retrying" : "Retry"}</button> : null}</section>;
  }
  const data = advisor.advisor;
  if (!data) return null;
  return <section className="border border-blue-200 bg-white">
    <div className="border-b border-blue-100 bg-blue-50 px-5 py-4"><div className="flex items-center gap-2 text-blue-700"><Strategy size={18} weight="fill" /><p className="text-xs font-semibold uppercase tracking-[0.14em]">Traditional methodology advisor</p></div><h2 className="mt-2 text-2xl font-semibold text-slate-950">{data.recommended_method}</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">{data.recommendation_summary}</p></div>
    <div className="grid gap-5 p-5 lg:grid-cols-2"><div><h3 className="text-sm font-semibold text-slate-900">Why this method fits</h3><p className="mt-2 text-sm leading-6 text-slate-700">{data.rationale}</p><h3 className="mt-5 text-sm font-semibold text-slate-900">Alternatives considered</h3><div className="mt-2 space-y-2">{data.alternatives.map((item) => <div key={item.method} className="border border-slate-200 px-3 py-2"><p className="text-sm font-semibold text-slate-800">{item.method}</p><p className="mt-1 text-sm text-slate-600">{item.reason}</p></div>)}</div></div><div><h3 className="text-sm font-semibold text-slate-900">Three-phase rollout</h3><ol className="mt-2 space-y-3">{data.rollout.map((phase, index) => <li key={`${phase.phase}-${index}`} className="border-l-2 border-blue-500 pl-3"><p className="text-sm font-semibold text-slate-800">{phase.phase}: {phase.objective}</p><p className="mt-1 text-sm text-slate-600">{phase.actions.join("; ")}</p>{phase.control_artifacts.length ? <p className="mt-1 text-xs text-slate-500">Controls: {phase.control_artifacts.join(", ")}</p> : null}</li>)}</ol><h3 className="mt-5 text-sm font-semibold text-slate-900">Tradeoffs</h3><ul className="mt-2 space-y-1 text-sm text-slate-600">{data.tradeoffs.map((item) => <li key={item}>{item}</li>)}</ul></div></div>
    {(data.evidence.length > 0 || data.limitations.length > 0) ? <div className="border-t border-slate-200 px-5 py-4"><h3 className="text-sm font-semibold text-slate-900">Evidence and limits</h3>{data.evidence.map((item) => <div key={item.claim} className="mt-3"><p className="text-sm text-slate-700">{item.claim}</p>{item.citations.map((citation, index) => <p key={`${citation.document_id}-${index}`} className="mt-1 flex items-center gap-1 text-xs text-slate-500"><FileText size={13} />{citation.filename}{citation.page_number ? `, page ${citation.page_number}` : ""}</p>)}</div>)}{data.limitations.map((item) => <p key={item} className="mt-2 text-xs text-slate-500">{item}</p>)}</div> : null}
  </section>;
}
