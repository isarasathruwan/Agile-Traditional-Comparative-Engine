"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle, FilePdf, LockKey, SpinnerGap, Trash, UploadSimple, Warning } from "@phosphor-icons/react";
import DocumentProcessingSteps from "@/components/DocumentProcessingSteps";
import {
  deleteDraftDocument,
  getDraftStatus,
  recordDraftConsent,
  startDocumentProcessing,
  uploadDocument,
  type DraftDocumentData,
  type DraftStatusResponse,
} from "@/lib/api";

interface DocumentUploadScreenProps {
  draftId: string;
  onContinue: () => void;
  onProcessingStarted: (status: DraftStatusResponse) => void;
  onSkip: () => void;
}

export default function DocumentUploadScreen({ draftId, onContinue, onProcessingStarted, onSkip }: DocumentUploadScreenProps) {
  const [status, setStatus] = useState<DraftStatusResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isConsenting, setIsConsenting] = useState(false);
  const [googleConsent, setGoogleConsent] = useState(false);
  const [researchAttestation, setResearchAttestation] = useState(false);
  const [consentRecorded, setConsentRecorded] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [removingDocumentId, setRemovingDocumentId] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const documents = status?.documents ?? [];
  const processing = status?.processing;
  const isProcessing = status?.status === "processing";
  const isReady = status?.status === "ready";
  const uploadsLocked = Boolean(status?.uploads_locked);
  const hasFailures = Boolean(processing && processing.failed_jobs > 0) || documents.some((document) => ["failed", "unsupported"].includes(document.status));

  const refreshStatus = useCallback(async () => {
    try {
      setStatus(await getDraftStatus(draftId));
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Unable to check document processing.");
    }
  }, [draftId]);

  useEffect(() => {
    const timer = window.setTimeout(() => void refreshStatus(), 0);
    return () => window.clearTimeout(timer);
  }, [refreshStatus]);

  useEffect(() => {
    if (!isProcessing) return;
    const timer = window.setInterval(() => void refreshStatus(), 1800);
    return () => window.clearInterval(timer);
  }, [isProcessing, refreshStatus]);

  const ensureConsent = async () => {
    if (consentRecorded) return true;
    if (!googleConsent || !researchAttestation) {
      setUploadError("Confirm both document-processing statements before selecting a PDF.");
      return false;
    }
    setIsConsenting(true);
    setUploadError(null);
    try {
      const nextStatus = await recordDraftConsent(draftId);
      setStatus(nextStatus);
      setConsentRecorded(true);
      return true;
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Unable to record document consent.");
      return false;
    } finally {
      setIsConsenting(false);
    }
  };

  const selectFile = async () => {
    if (uploadsLocked) return;
    if (await ensureConsent()) fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (uploadsLocked) {
      setUploadError("The document set is locked because analysis has started.");
      return;
    }
    if (file.type !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Upload a text-based PDF. Scanned PDFs are not supported in this release.");
      return;
    }
    if (documents.length >= 5) {
      setUploadError("Maximum of five files allowed.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("File size must be under 10 MB.");
      return;
    }
    setIsUploading(true);
    setUploadError(null);
    try {
      await uploadDocument(draftId, file);
      setStatus(await getDraftStatus(draftId));
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Failed to upload document.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeDocument = async (documentId: number) => {
    setRemovingDocumentId(documentId);
    setUploadError(null);
    try {
      setStatus(await deleteDraftDocument(draftId, documentId));
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Unable to remove document.");
    } finally {
      setRemovingDocumentId(null);
    }
  };

  const startAnalysis = async () => {
    setIsStarting(true);
    setUploadError(null);
    try {
      const nextStatus = await startDocumentProcessing(draftId);
      setStatus(nextStatus);
      onProcessingStarted(nextStatus);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Unable to start document analysis.");
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <section
      className="w-full border-y border-slate-200 bg-white px-5 py-8 sm:border sm:px-10 sm:py-11"
    >
      <div className="max-w-2xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Document evidence</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-[2.15rem]">Attach a project PDF</h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Add every supporting PDF before analysis. Files remain encrypted while you build the document set.
        </p>
      </div>

      <div className="mt-7 divide-y divide-slate-200 border-y border-slate-200">
        <label className="flex gap-3 py-4 text-sm text-slate-700">
          <input type="checkbox" checked={googleConsent} onChange={(event) => setGoogleConsent(event.target.checked)} className="mt-0.5 h-4 w-4 accent-blue-700" />
          <span>I agree that this PDF may be processed by Google AI to generate embeddings and evidence suggestions.</span>
        </label>
        <label className="flex gap-3 py-4 text-sm text-slate-700">
          <input type="checkbox" checked={researchAttestation} onChange={(event) => setResearchAttestation(event.target.checked)} className="mt-0.5 h-4 w-4 accent-blue-700" />
          <span>I confirm that this is anonymized research material and contains no confidential or personal data.</span>
        </label>
      </div>

      <div className="mt-6 border border-dashed border-blue-300 bg-blue-50/60 p-7 text-center sm:p-9">
        <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="application/pdf,.pdf" className="hidden" />
        <FilePdf size={38} className="mx-auto text-blue-700" weight="duotone" />
        <p className="mt-4 text-base font-semibold text-slate-900">Text-based PDF only</p>
        <p className="mt-2 text-sm text-slate-500">Up to 10 MB per file. Five files per assessment. Exact duplicates are blocked.</p>
        <button
          type="button"
          onClick={() => void selectFile()}
          disabled={uploadsLocked || isUploading || isConsenting || documents.length >= 5}
          className="mt-5 inline-flex items-center gap-2 rounded-md border border-blue-200 bg-white px-5 py-3 text-sm font-semibold text-blue-800 transition-colors hover:border-blue-500 hover:bg-blue-50 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isUploading || isConsenting ? <SpinnerGap size={16} className="animate-spin" /> : <UploadSimple size={16} />}
          {uploadsLocked ? "Document set locked" : isUploading ? "Uploading PDF" : isConsenting ? "Saving consent" : "Select PDF"}
        </button>
      </div>

      {isProcessing ? (
        <div className="mt-6 border-y border-blue-200 bg-blue-50/50" role="status" aria-live="polite">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-blue-200 px-4 py-4">
            <div className="flex min-w-0 items-start gap-3">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-blue-200 bg-white text-blue-700 shadow-[inset_0_1px_0_rgba(255,255,255,0.95)]">
                <SpinnerGap size={16} className="animate-spin" weight="bold" />
              </span>
              <div>
                <p className="text-sm font-semibold text-blue-950">Analyzing your document</p>
                <p className="mt-1 text-sm text-blue-900/80">You can keep answering questions while this finishes.</p>
              </div>
            </div>
              <span className="font-mono text-xs font-semibold text-blue-800">
                {documents.length} document{documents.length === 1 ? "" : "s"}
            </span>
          </div>
          <div className="px-4 py-1"><DocumentProcessingSteps currentStage={processing?.current_stage ?? "queued"} /></div>
        </div>
      ) : null}

      {uploadError ? (
        <div className="mt-5 flex gap-2 border-l-2 border-rose-500 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          <Warning size={17} className="mt-0.5 shrink-0" />
          <p>{uploadError}</p>
        </div>
      ) : null}

      {hasFailures ? (
        <div className="mt-5 flex gap-2 border-l-2 border-amber-500 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <Warning size={17} className="mt-0.5 shrink-0" />
          <p>One or more documents could not be processed. You can continue with the remaining evidence or complete the assessment manually.</p>
        </div>
      ) : null}

      {documents.length > 0 ? (
        <ul className="mt-6 divide-y divide-slate-200 border-y border-slate-200">
          {documents.map((document: DraftDocumentData) => (
            <li key={document.id} className="flex items-center justify-between gap-4 py-4">
              <div className="flex min-w-0 items-center gap-3">
                <FilePdf size={20} className="shrink-0 text-blue-700" />
                <span className="truncate text-sm font-semibold text-slate-800">{document.filename}</span>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                  {document.status === "processed" ? <CheckCircle size={14} className="text-blue-700" weight="fill" /> : <LockKey size={14} className="text-slate-500" />}
                  {document.status === "processed"
                    ? "Ready"
                    : ["failed", "unsupported"].includes(document.status)
                      ? "Needs attention"
                      : document.status === "uploaded"
                        ? "Ready to analyze"
                        : "Analyzing"}
                </span>
                {!uploadsLocked ? (
                  <button
                    type="button"
                    onClick={() => void removeDocument(document.id)}
                    disabled={removingDocumentId === document.id}
                    className="inline-flex h-8 w-8 items-center justify-center text-slate-500 transition-colors hover:bg-rose-50 hover:text-rose-700 disabled:opacity-50"
                    aria-label={`Remove ${document.filename}`}
                    title="Remove document"
                  >
                    <Trash size={17} />
                  </button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-8 flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row">
        <button
          type="button"
          onClick={() => {
            if (isReady) onContinue();
            else if (documents.length > 0 && !uploadsLocked) void startAnalysis();
            else onSkip();
          }}
          disabled={isProcessing || isStarting}
          className="flex-1 rounded-md bg-blue-700 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-800 active:translate-y-px disabled:cursor-wait disabled:bg-slate-400"
        >
          {isProcessing
            ? "Processing evidence"
            : isStarting
              ? "Starting analysis"
              : isReady
                ? "Continue to methodology questions"
                : uploadsLocked
                  ? "Continue without documents"
                  : documents.length > 0
                    ? `Analyze ${documents.length} document${documents.length === 1 ? "" : "s"}`
                    : "Continue without documents"}
        </button>
        {documents.length === 0 ? (
          <button type="button" onClick={onSkip} className="rounded-md border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:border-blue-300 hover:bg-blue-50">
            Skip
          </button>
        ) : null}
      </div>
    </section>
  );
}
