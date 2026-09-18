"use client";

import { Warning } from "@phosphor-icons/react";
import DocumentProcessingSteps from "@/components/DocumentProcessingSteps";
import type { DraftStatusResponse } from "@/lib/api";

interface DocumentProcessingWaitProps {
  status: DraftStatusResponse | null;
  refreshError?: string | null;
}

export default function DocumentProcessingWait({ status, refreshError }: DocumentProcessingWaitProps) {
  const isFailed = status?.status === "failed";

  return (
    <section className="w-full border-y border-slate-200 bg-white px-5 py-8 sm:border sm:px-10 sm:py-11" role="status" aria-live="polite">
      <div className={`border-l-2 pl-5 ${isFailed ? "border-amber-500" : "border-blue-700"}`}>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Document evidence</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-[2.15rem]">
          {isFailed ? "Continue with questionnaire evidence" : "Your answers are saved"}
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
          {isFailed
            ? "Document processing could not finish, so we will prepare the assessment from your questionnaire answers."
            : "We are finishing the document analysis before asking you to review its cited suggestions."}
        </p>
      </div>

      {!isFailed ? <DocumentProcessingSteps currentStage={status?.processing.current_stage ?? "queued"} /> : null}

      {refreshError ? (
        <div className="mt-6 flex gap-2 border-l-2 border-amber-500 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <Warning size={17} className="mt-0.5 shrink-0" />
          <p>{refreshError}</p>
        </div>
      ) : null}
    </section>
  );
}
