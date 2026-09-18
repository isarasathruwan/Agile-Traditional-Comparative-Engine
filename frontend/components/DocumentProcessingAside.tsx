"use client";

import { CheckCircle, SpinnerGap, Warning } from "@phosphor-icons/react";
import DocumentProcessingSteps from "@/components/DocumentProcessingSteps";
import type { DraftStatusResponse } from "@/lib/api";

interface DocumentProcessingAsideProps {
  status: DraftStatusResponse;
  refreshError?: string | null;
}

export default function DocumentProcessingAside({ status, refreshError }: DocumentProcessingAsideProps) {
  const { processing } = status;
  const isProcessing = status.status === "processing";
  const isReady = status.status === "ready";
  const totalDocuments = Math.max(processing.total_documents, status.documents.length);

  return (
    <section className="mt-7 border-t border-slate-200 pt-5" aria-label="Document evidence status">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-600">Document evidence</p>
      <div
        className={`mt-3 border-l-2 pl-3 ${
          isReady ? "border-blue-700" : isProcessing ? "border-blue-400" : "border-amber-500"
        }`}
        role="status"
        aria-live="polite"
      >
        <div className="flex items-start gap-2">
          {isReady ? (
            <CheckCircle size={17} className="mt-0.5 shrink-0 text-blue-700" weight="fill" />
          ) : isProcessing ? (
            <SpinnerGap size={17} className="mt-0.5 shrink-0 animate-spin text-blue-700" weight="bold" />
          ) : (
            <Warning size={17} className="mt-0.5 shrink-0 text-amber-700" weight="fill" />
          )}
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-900">
              {isReady ? "Suggestions ready" : isProcessing ? "Analyzing your document" : "Suggestions unavailable"}
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              {isReady
                ? "You will review the suggestions after the methodology questions."
                : isProcessing
                  ? `You can keep answering while we review ${totalDocuments} document${totalDocuments === 1 ? "" : "s"}.`
                  : "Your questionnaire answers can still be used to complete the assessment."}
            </p>
          </div>
        </div>

        {isProcessing ? <DocumentProcessingSteps currentStage={processing.current_stage} compact /> : null}

        {refreshError ? <p className="mt-3 text-xs leading-5 text-amber-800">{refreshError}</p> : null}
      </div>
    </section>
  );
}
