"use client";

import { CheckCircle, FileText, SpinnerGap, Warning } from "@phosphor-icons/react";
import { useState } from "react";
import type { EvidenceAnswerData } from "@/lib/api";

interface EvidenceAnswerReviewProps {
  answers: EvidenceAnswerData[];
  onComplete: (confirmedQuestionKeys: string[]) => Promise<void>;
}

export default function EvidenceAnswerReview({ answers, onComplete }: EvidenceAnswerReviewProps) {
  const candidates = answers.filter(
    (item) =>
      item.construct &&
      item.answer_type === "likert" &&
      item.evidence_status === "suggested" &&
      item.proposed_value &&
      item.citations.length > 0
  );
  const [included, setIncluded] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(candidates.map((item) => [item.question_key, true]))
  );
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await onComplete(candidates.filter((item) => included[item.question_key]).map((item) => item.question_key));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save document evidence.");
      setIsSaving(false);
    }
  };

  return (
    <section className="w-full border-y border-slate-200 bg-white px-5 py-8 sm:border sm:px-10 sm:py-11">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Evidence review</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-[2.15rem]">Confirm document-backed signals</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
        Only cited document evidence can adjust the decision. Include a suggestion to use its extracted score, or leave it out of the assessment.
      </p>

      {candidates.length === 0 ? (
        <div className="mt-8 border-l-2 border-slate-300 bg-slate-50 px-4 py-4 text-sm text-slate-600">
          No citable document-only signals are available. Continue with the questionnaire answers.
        </div>
      ) : (
        <div className="mt-8 divide-y divide-slate-200 border-y border-slate-200">
          {candidates.map((item) => (
            <article key={item.question_key} className="py-5">
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_180px] lg:items-start">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-900">{item.prompt ?? item.question_key}</p>
                  {item.citations.map((citation) => (
                    <div key={`${citation.document_id}-${citation.page_number}-${citation.excerpt.slice(0, 24)}`} className="mt-3 border-l-2 border-blue-200 pl-3">
                      <div className="flex min-w-0 items-center gap-2 text-xs font-semibold text-slate-500"><FileText size={14} className="shrink-0" /><span className="min-w-0 break-words">{citation.filename} · page {citation.page_number}</span></div>
                      <p className="mt-1 text-justify text-sm leading-6 text-slate-600">{citation.excerpt}</p>
                    </div>
                  ))}
                </div>
                <div className="space-y-3 lg:justify-self-end">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1 lg:justify-end">
                    <span className="text-xs font-semibold text-blue-700">{item.confidence} confidence</span>
                    <span className="text-xs font-semibold text-slate-500">{item.construct}</span>
                  </div>
                  <label className="flex w-full items-start gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700 lg:w-[180px]">
                    <input
                      type="checkbox"
                      checked={included[item.question_key] ?? false}
                      onChange={(event) => setIncluded((previous) => ({ ...previous, [item.question_key]: event.target.checked }))}
                      className="mt-0.5 h-4 w-4 accent-blue-700"
                    />
                    <span className="min-w-0 flex-1 text-right"><span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Extracted score</span><span className="mt-1 block text-lg font-semibold text-slate-900">{item.proposed_value} / 5</span><span className="mt-1 block text-xs text-slate-500">Include in decision</span></span>
                  </label>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {error ? <div className="mt-5 flex gap-2 border-l-2 border-rose-500 bg-rose-50 px-4 py-3 text-sm text-rose-800"><Warning size={17} className="mt-0.5" />{error}</div> : null}

      <div className="mt-8 flex justify-end border-t border-slate-200 pt-6">
        <button type="button" onClick={() => void submit()} disabled={isSaving} className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-800 active:translate-y-px disabled:bg-slate-400">
          {isSaving ? <SpinnerGap size={16} className="animate-spin" /> : <CheckCircle size={16} weight="bold" />}
          {isSaving ? "Saving evidence" : "Continue to assessment review"}
        </button>
      </div>
    </section>
  );
}
