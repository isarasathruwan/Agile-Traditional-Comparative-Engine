"use client";

import {
  ChartBar,
  CaretLeft,
  CaretRight,
  CheckCircle,
  FileText,
  FlagBanner,
  ShieldCheck,
  Strategy,
  Warning,
  X,
} from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import {
  getDocumentExtractions,
  getDocumentPreview,
  getDraftStatus,
  type AssessmentCreateResponse,
  type DocumentExtractedFactData,
  type DraftDocumentData,
} from "@/lib/api";
import DecisionDriverChart from "@/components/results/DecisionDriverChart";
import DecisionVisualSummary from "@/components/results/DecisionVisualSummary";
import EvidenceContributionPanel from "@/components/results/EvidenceContributionPanel";
import RadarComparisonChart from "@/components/results/RadarComparisonChart";
import TraditionalAdvisorPanel from "@/components/results/TraditionalAdvisorPanel";

type WorkspaceTab = "decision" | "plan" | "evidence" | "analysis";
type AnalysisMode = "fit" | "dimensions" | "research";
type EvidenceMode = "answers" | "facts" | "documents";
type AnswerSection = "Project context" | "Method signals";
type DialogContent = "trace" | "metadata" | "excerpt" | null;

export type ResultQuestionAnswer = {
  key: string;
  section: "Project context" | "Method signals";
  prompt: string;
  value: string;
};

type Props = {
  result: AssessmentCreateResponse;
  name: string;
  draftId: string | null;
  questions: ResultQuestionAnswer[];
  onRestart: () => void;
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

const formatLabel = (value: string) =>
  DECISION_SIGNAL_LABELS[value]
  ?? value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

export default function ResultWorkspace({ result, name, draftId, questions, onRestart }: Props) {
  const evidenceAnswers = result.evidence_answers ?? [];
  const confirmedDocumentEvidence = evidenceAnswers.filter((item) => item.final_source === "confirmed_document");
  const evidenceScoring = result.evidence_scoring;
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("decision");
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("fit");
  const [profileMapOpen, setProfileMapOpen] = useState(false);
  const [evidenceMode, setEvidenceMode] = useState<EvidenceMode>("answers");
  const [answerSection, setAnswerSection] = useState<AnswerSection>("Project context");
  const [mobileSignalIndex, setMobileSignalIndex] = useState(0);
  const [selectedQuestionKey, setSelectedQuestionKey] = useState(evidenceAnswers[0]?.question_key ?? questions[0]?.key ?? "");
  const [selectedPracticeKey, setSelectedPracticeKey] = useState(result.decision_report.strategy_profile.strategy_options[0]?.key ?? "");
  const [dialogContent, setDialogContent] = useState<DialogContent>(null);
  const [facts, setFacts] = useState<DocumentExtractedFactData[]>([]);
  const [documents, setDocuments] = useState<DraftDocumentData[]>([]);
  const [documentError, setDocumentError] = useState<string | null>(null);
  const [factsError, setFactsError] = useState<string | null>(null);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [documentLoadAttempt, setDocumentLoadAttempt] = useState(0);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [selectedFactId, setSelectedFactId] = useState<number | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewTitle, setPreviewTitle] = useState("");
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  useEffect(() => {
    if (!draftId) return;
    let active = true;
    const loadDocumentDetails = async () => {
      setIsLoadingDocuments(true);
      setDocumentError(null);
      setFactsError(null);
      try {
        const status = await getDraftStatus(draftId);
        if (!active) return;
        setDocuments(status.documents);
        setSelectedDocumentId((current) => current ?? status.documents[0]?.id ?? null);
      } catch (error) {
        if (active) {
          setDocumentError(error instanceof Error ? error.message : "Unable to load document details.");
          setIsLoadingDocuments(false);
        }
        return;
      }
      try {
        const extractedFacts = await getDocumentExtractions(draftId);
        if (!active) return;
        setFacts(extractedFacts);
        setSelectedFactId((current) => current ?? extractedFacts[0]?.id ?? null);
      } catch (error) {
        if (active) setFactsError(error instanceof Error ? error.message : "Unable to load extracted document facts.");
      } finally {
        if (active) setIsLoadingDocuments(false);
      }
    };
    void loadDocumentDetails();
    return () => {
      active = false;
    };
  }, [draftId, documentLoadAttempt]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const report = result.decision_report;
  const strategy = report.strategy_profile;
  const selectedEvidence = evidenceAnswers.find((item) => item.question_key === selectedQuestionKey);
  const selectedQuestion = questions.find((item) => item.key === selectedQuestionKey) ?? questions[0];
  const selectedFact = facts.find((item) => item.id === selectedFactId) ?? facts[0];
  const selectedDocument = documents.find((item) => item.id === selectedDocumentId) ?? documents[0];
  const selectedPractice = strategy.strategy_options.find((item) => item.key === selectedPracticeKey) ?? strategy.strategy_options[0];
  const selectedCitation = selectedEvidence?.citations[0];
  const strongestDriver = report.drivers[0];
  const primaryWatch = report.risk_flags[0]?.label ?? report.tradeoffs.watch_areas[0];
  const nextAction = report.next_steps[0];
  const projectSnapshot = ["Q7", "Q8", "Q9", "Q10"]
    .map((key) => questions.find((question) => question.key === key))
    .filter((question): question is ResultQuestionAnswer => Boolean(question));
  const visibleQuestions = questions.filter((question) => question.section === answerSection);
  const selectedQuestionIndex = Math.max(
    0,
    visibleQuestions.findIndex((question) => question.key === selectedQuestionKey),
  );
  const decisionSignals = [
    {
      key: "driver",
      icon: Strategy,
      label: "Primary driver",
      body: strongestDriver ? `${strongestDriver.label} (${strongestDriver.score.toFixed(2)}/5)` : "Method fit is based on the confirmed project signals.",
    },
    {
      key: "watch",
      icon: primaryWatch ? FlagBanner : CheckCircle,
      label: primaryWatch ? "Watch area" : "Decision status",
      body: primaryWatch ?? "No additional risk signal was triggered.",
    },
    {
      key: "next",
      icon: Warning,
      label: "Next action",
      body: nextAction ?? "Review the recommendation with the project stakeholders.",
    },
    {
      key: "evidence",
      icon: FileText,
      label: "Assessment basis",
      body: confirmedDocumentEvidence.length
        ? `${confirmedDocumentEvidence.length} confirmed document-only signals adjusted the decision within its evidence cap.`
        : "The recommendation uses the confirmed project context and methodology signals.",
    },
  ];

  const openDocumentPreview = async (document: DraftDocumentData) => {
    if (!draftId) return;
    setPreviewError(null);
    setIsPreviewLoading(true);
    try {
      const blob = await getDocumentPreview(draftId, document.id);
      setPreviewTitle(document.filename);
      setPreviewUrl(URL.createObjectURL(blob));
    } catch (error) {
      setPreviewError(error instanceof Error ? error.message : "Unable to prepare the document preview.");
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const closePreview = () => {
    setPreviewUrl(null);
    setPreviewError(null);
  };

  const tabs: Array<{ key: WorkspaceTab; label: string; icon: typeof Strategy }> = [
    { key: "decision", label: "Decision", icon: CheckCircle },
    { key: "plan", label: "Plan", icon: Strategy },
    { key: "evidence", label: "Evidence", icon: FileText },
    { key: "analysis", label: "Analysis", icon: ChartBar },
  ];

  return (
    <main className="h-[100dvh] min-h-[100dvh] overflow-hidden bg-[#f6f8fc] text-slate-900">
      <div className="grid h-full grid-rows-[auto_auto_minmax(0,1fr)_auto]">
        <header className="flex min-h-16 items-center justify-between gap-5 border-b border-slate-200 bg-[#f6f8fc] px-4 py-3 sm:px-6 lg:px-8 xl:px-12">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">MethodAlign</p>
            <p className="truncate text-sm font-medium text-slate-600">Project methodology decision</p>
          </div>
          <button
            type="button"
            onClick={onRestart}
            className="shrink-0 border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition-colors hover:border-blue-300 hover:text-blue-700 active:translate-y-px"
          >
            New assessment
          </button>
        </header>

        <nav aria-label="Assessment result sections" className="border-b border-slate-200 bg-white px-4 sm:px-6 lg:px-8 xl:px-12">
          <div role="tablist" aria-label="Assessment result sections" className="grid grid-cols-4">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const selected = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  id={`result-tab-${tab.key}`}
                  type="button"
                  role="tab"
                  aria-label={tab.label}
                  aria-selected={selected}
                  aria-controls={`result-panel-${tab.key}`}
                  onClick={() => setActiveTab(tab.key)}
                  title={tab.label}
                  className={[
                    "flex min-h-12 items-center justify-center gap-2 border-b-2 px-2 text-sm font-semibold transition-colors sm:justify-start sm:px-4",
                    selected ? "border-blue-700 text-blue-700" : "border-transparent text-slate-500 hover:text-slate-900",
                  ].join(" ")}
                >
                  <Icon size={17} weight={selected ? "fill" : "regular"} aria-hidden="true" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        <section className="min-h-0 px-4 py-4 sm:px-6 sm:py-5 lg:px-8 xl:px-12">
          <div className="h-full min-h-0 overflow-hidden border border-slate-200 bg-white">
            {activeTab === "decision" ? (
              <section id="result-panel-decision" role="tabpanel" aria-labelledby="result-tab-decision" className="grid h-full min-h-0 overflow-y-auto lg:grid-cols-[minmax(0,1.45fr)_minmax(290px,0.8fr)] lg:overflow-hidden">
                <div className="flex min-h-0 flex-col p-5 sm:p-7 lg:overflow-y-auto lg:p-8">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Recommended direction</p>
                  <h1 className="mt-3 max-w-4xl text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                    Use {result.recommendation} for{name ? ` ${name}'s` : " this"} project.
                  </h1>
                  <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{report.methodology_fit_summary}</p>

                  <div className="mt-6">
                    <DecisionVisualSummary
                      agileScore={result.agile_score}
                      traditionalScore={result.traditional_score}
                      recommendation={result.recommendation}
                      scoreGap={result.insights.score_gap}
                    />
                  </div>

                  {confirmedDocumentEvidence.length > 0 ? (
                    <EvidenceContributionPanel
                      confirmedItemCount={confirmedDocumentEvidence.length}
                      documentEvidenceCap={evidenceScoring.document_evidence_cap}
                      documentCoverage={evidenceScoring.document_coverage}
                      documentContribution={evidenceScoring.document_contribution}
                      onReviewEvidence={() => setActiveTab("evidence")}
                    />
                  ) : null}

                  <div className="mt-6 grid grid-cols-2 border-y border-slate-200 sm:grid-cols-4">
                    {projectSnapshot.map((item) => (
                      <div key={item.key} className="border-b border-slate-200 px-0 py-3 last:border-b-0 sm:border-b-0 sm:border-r sm:px-4 sm:last:border-r-0">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{item.prompt}</p>
                        <p className="mt-1.5 text-sm font-semibold leading-5 text-slate-800">{item.value}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <aside className="min-h-0 border-t border-slate-200 bg-slate-50/70 p-5 sm:p-7 lg:overflow-y-auto lg:border-l lg:border-t-0 lg:p-8">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Decision signals</p>
                  <div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">
                    {decisionSignals.map((signal, index) => (
                      <div key={signal.key} className={index === mobileSignalIndex ? "block" : "hidden lg:block"}>
                        <SignalRow icon={signal.icon} label={signal.label} body={signal.body} />
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex items-center justify-between lg:hidden">
                    <button type="button" aria-label="Previous decision signal" onClick={() => setMobileSignalIndex((index) => (index + decisionSignals.length - 1) % decisionSignals.length)} className="p-1.5 text-slate-500 hover:text-blue-700"><CaretLeft size={18} /></button>
                    <span className="font-mono text-xs text-slate-500">{mobileSignalIndex + 1} / {decisionSignals.length}</span>
                    <button type="button" aria-label="Next decision signal" onClick={() => setMobileSignalIndex((index) => (index + 1) % decisionSignals.length)} className="p-1.5 text-slate-500 hover:text-blue-700"><CaretRight size={18} /></button>
                  </div>
                  <button type="button" onClick={() => setActiveTab("plan")} className="mt-5 text-sm font-semibold text-blue-700 hover:text-blue-900">
                    Review delivery plan
                  </button>
                </aside>
              </section>
            ) : null}

            {activeTab === "plan" ? (
              <section id="result-panel-plan" role="tabpanel" aria-labelledby="result-tab-plan" className="h-full min-h-0 overflow-y-auto">
                {result.recommendation === "Traditional" ? <div className="p-5 sm:p-7 lg:p-8"><TraditionalAdvisorPanel submissionId={result.submission_id} initial={result.traditional_advisor} /></div> : null}
                <div className="grid lg:grid-cols-[minmax(0,1.12fr)_minmax(320px,0.88fr)]">
                <div className="min-h-0 p-5 sm:p-7 lg:p-8">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Delivery plan</p>
                  <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
                    <h2 className="text-2xl font-semibold tracking-tight text-slate-950">{formatLabel(strategy.delivery_strategy)}</h2>
                    <span className="font-mono text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{strategy.hybrid_readiness.level} hybrid readiness</span>
                  </div>
                  <ol className="mt-5 divide-y divide-slate-200 border-y border-slate-200">
                    {report.next_steps.slice(0, 3).map((step, index) => (
                      <li key={step} className="grid grid-cols-[34px_minmax(0,1fr)] gap-3 py-3.5">
                        <span className="font-mono text-sm font-semibold text-blue-700">{String(index + 1).padStart(2, "0")}</span>
                        <span className="text-sm leading-5 text-slate-700">{step}</span>
                      </li>
                    ))}
                  </ol>
                  <div className="mt-5">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Advisory practices</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {strategy.strategy_options.slice(0, 5).map((option) => (
                        <button
                          key={option.key}
                          type="button"
                          onClick={() => setSelectedPracticeKey(option.key)}
                          className={[
                            "border px-3 py-2 text-sm font-semibold transition-colors active:translate-y-px",
                            selectedPractice?.key === option.key ? "border-blue-700 bg-blue-50 text-blue-800" : "border-slate-300 bg-white text-slate-600 hover:border-blue-300",
                          ].join(" ")}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                    {selectedPractice ? <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">{selectedPractice.reason}</p> : null}
                  </div>
                </div>

                <aside className="min-h-0 border-t border-slate-200 bg-slate-50/70 p-5 sm:p-7 lg:border-l lg:border-t-0 lg:p-8">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Governance controls</p>
                  <div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">
                    {strategy.governance_controls.slice(0, 4).map((control) => (
                      <p key={control} className="flex gap-3 py-3.5 text-sm leading-5 text-slate-700">
                        <ShieldCheck size={18} weight="bold" className="mt-0.5 shrink-0 text-blue-700" aria-hidden="true" />
                        {control}
                      </p>
                    ))}
                  </div>
                  <div className="mt-6">
                    <div className="flex items-end justify-between gap-3">
                      <p className="text-sm font-semibold text-slate-900">Hybrid readiness</p>
                      <p className="font-mono text-sm font-semibold text-slate-700">{strategy.hybrid_readiness.score}/100</p>
                    </div>
                    <div className="mt-3 h-1.5 bg-slate-200"><div className="h-full bg-blue-700" style={{ width: `${strategy.hybrid_readiness.score}%` }} /></div>
                  </div>
                </aside>
                </div>
              </section>
            ) : null}

            {activeTab === "evidence" ? (
              <section id="result-panel-evidence" role="tabpanel" aria-labelledby="result-tab-evidence" className="flex h-full min-h-0 flex-col">
                <div className="flex min-h-14 items-center justify-between gap-3 border-b border-slate-200 px-5 sm:px-7 lg:px-8">
                  <div className="flex gap-1" aria-label="Evidence view">
                    {(["answers", "facts", "documents"] as EvidenceMode[]).map((mode) => (
                      <button
                        key={mode}
                        type="button"
                        onClick={() => setEvidenceMode(mode)}
                        className={[
                          "px-2 py-2 text-sm font-semibold capitalize transition-colors sm:px-3",
                          evidenceMode === mode ? "text-blue-700" : "text-slate-500 hover:text-slate-900",
                        ].join(" ")}
                      >
                        {mode === "facts" ? "Extracted facts" : mode}
                      </button>
                    ))}
                  </div>
                  {evidenceMode === "answers" && evidenceAnswers.length > 0 ? (
                    <button type="button" onClick={() => setDialogContent("trace")} className="text-sm font-semibold text-blue-700 hover:text-blue-900">Processing trace</button>
                  ) : null}
                </div>

                {evidenceMode === "answers" ? (
                  <div className="grid min-h-0 flex-1 lg:grid-cols-[minmax(300px,1.05fr)_minmax(260px,0.75fr)]">
                    <div className="min-h-0 p-5 sm:p-7 lg:p-8">
                      <div className="flex items-end justify-between gap-3">
                        <div>
                          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Confirmed answers</p>
                          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">Project brief and method signals</h2>
                        </div>
                        <span className="font-mono text-xs text-slate-500">{questions.length} answers</span>
                      </div>
                      {confirmedDocumentEvidence.length > 0 ? (
                        <div className="mt-4 divide-y divide-blue-100 border-y border-blue-100 bg-blue-50/40">
                          {confirmedDocumentEvidence.map((item) => (
                            <div key={item.question_key} className="grid gap-2 px-3 py-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                              <div><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-blue-700">Document-only · {item.construct}</p><p className="mt-1 text-sm font-semibold text-slate-900">{item.prompt ?? item.question_key}</p></div>
                              <p className="font-mono text-sm font-semibold text-slate-900">{item.final_value} / 5</p>
                            </div>
                          ))}
                        </div>
                      ) : null}
                      <div className="mt-5 flex gap-2 border-b border-slate-200">
                        {(["Project context", "Method signals"] as AnswerSection[]).map((section) => (
                          <button
                            key={section}
                            type="button"
                            onClick={() => {
                              setAnswerSection(section);
                              setSelectedQuestionKey(questions.find((question) => question.section === section)?.key ?? "");
                            }}
                            className={[
                              "border-b-2 px-2 pb-2 text-sm font-semibold transition-colors",
                              answerSection === section ? "border-blue-700 text-blue-700" : "border-transparent text-slate-500 hover:text-slate-900",
                            ].join(" ")}
                          >
                            {section}
                          </button>
                        ))}
                      </div>
                      <div className="mt-3 hidden grid-cols-2 divide-x divide-y divide-slate-200 border border-slate-200 sm:grid">
                        {visibleQuestions.map((question) => {
                          const evidence = evidenceAnswers.find((item) => item.question_key === question.key);
                          const selected = question.key === selectedQuestionKey;
                          return (
                            <button
                              key={question.key}
                              type="button"
                              onClick={() => setSelectedQuestionKey(question.key)}
                              className={[
                                "min-h-[72px] p-3 text-left transition-colors",
                                selected ? "bg-blue-50" : "bg-white hover:bg-slate-50",
                              ].join(" ")}
                            >
                              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{question.key}</p>
                              <p className="mt-1 line-clamp-1 text-xs text-slate-600">{question.prompt}</p>
                              <p className="mt-1 text-sm font-semibold text-slate-900">{question.value}</p>
                              {evidence ? <p className="mt-1 text-[10px] font-semibold capitalize text-blue-700">{evidence.confidence} document evidence</p> : null}
                            </button>
                          );
                        })}
                      </div>
                      <div className="mt-4 border-y border-slate-200 py-4 sm:hidden">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{selectedQuestion?.key}</p>
                        <p className="mt-2 text-sm leading-5 text-slate-700">{selectedQuestion?.prompt}</p>
                        <p className="mt-2 text-xl font-semibold text-slate-950">{selectedQuestion?.value}</p>
                        <div className="mt-4 flex items-center justify-between">
                          <button type="button" aria-label="Previous answer" onClick={() => setSelectedQuestionKey(visibleQuestions[(selectedQuestionIndex + visibleQuestions.length - 1) % visibleQuestions.length]?.key ?? "")} className="p-1.5 text-slate-500 hover:text-blue-700"><CaretLeft size={18} /></button>
                          <span className="font-mono text-xs text-slate-500">{selectedQuestionIndex + 1} / {visibleQuestions.length}</span>
                          <button type="button" aria-label="Next answer" onClick={() => setSelectedQuestionKey(visibleQuestions[(selectedQuestionIndex + 1) % visibleQuestions.length]?.key ?? "")} className="p-1.5 text-slate-500 hover:text-blue-700"><CaretRight size={18} /></button>
                        </div>
                      </div>
                    </div>
                    <aside className="min-h-0 border-t border-slate-200 bg-slate-50/70 p-5 sm:p-7 lg:border-l lg:border-t-0 lg:p-8">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Answer basis</p>
                      <h3 className="mt-2 text-lg font-semibold text-slate-950">{selectedQuestion?.key} · {selectedQuestion?.value}</h3>
                      <p className="mt-3 text-sm leading-6 text-slate-600">{selectedQuestion?.prompt}</p>
                      {selectedEvidence ? (
                        <>
                          <div className="mt-5 border-y border-slate-200 py-4">
                            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Document confirmation</p>
                            <p className="mt-2 text-sm font-semibold capitalize text-slate-900">{selectedEvidence.confidence} confidence · {selectedEvidence.final_source === "user_override" ? "Participant adjusted" : "Participant confirmed"}</p>
                          </div>
                          {selectedCitation ? (
                            <div className="mt-4 border-l-2 border-blue-300 bg-blue-50/60 px-4 py-3">
                              <p className="flex items-center gap-2 text-xs font-semibold text-slate-600"><FileText size={15} />{selectedCitation.filename} · page {selectedCitation.page_number}</p>
                              <p className="mt-2 line-clamp-4 text-sm leading-6 text-slate-700">{selectedCitation.excerpt}</p>
                              <button type="button" onClick={() => setDialogContent("excerpt")} className="mt-2 text-sm font-semibold text-blue-700 hover:text-blue-900">Open excerpt</button>
                            </div>
                          ) : null}
                        </>
                      ) : <p className="mt-5 border-y border-slate-200 py-4 text-sm leading-6 text-slate-600">This answer was supplied during the assessment and has no supporting document citation.</p>}
                    </aside>
                  </div>
                ) : null}

                {evidenceMode === "facts" ? (
                  <div className="grid min-h-0 flex-1 lg:grid-cols-[minmax(300px,1.05fr)_minmax(260px,0.75fr)]">
                    <div className="min-h-0 p-5 sm:p-7 lg:p-8">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Extracted document facts</p>
                      <div className="mt-2 flex items-end justify-between gap-3"><h2 className="text-2xl font-semibold tracking-tight text-slate-950">Source-backed project observations</h2><span className="font-mono text-xs text-slate-500">{facts.length} facts</span></div>
                      {isLoadingDocuments ? <p className="mt-8 text-sm text-slate-500">Loading document facts...</p> : null}
                      {factsError ? <p className="mt-4 text-sm text-red-700">{factsError}</p> : null}
                      {!isLoadingDocuments && facts.length === 0 ? <p className="mt-8 max-w-xl text-sm leading-6 text-slate-600">No structured facts are available for the uploaded documents. The assessment evidence and original documents remain available in the other views.</p> : null}
                      {facts.length > 0 ? <div className="mt-5 grid grid-cols-1 divide-y divide-slate-200 border-y border-slate-200 sm:grid-cols-2 sm:divide-x">
                        {facts.map((fact) => <button key={fact.id} type="button" onClick={() => setSelectedFactId(fact.id)} className={["min-h-[76px] p-3 text-left transition-colors", selectedFact?.id === fact.id ? "bg-blue-50" : "hover:bg-slate-50"].join(" ")}><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-blue-700">{formatLabel(fact.category)}</p><p className="mt-1 text-sm font-semibold text-slate-900">{fact.label}</p><p className="mt-1 line-clamp-1 text-sm text-slate-600">{fact.value}</p></button>)}
                      </div> : null}
                    </div>
                    <aside className="min-h-0 border-t border-slate-200 bg-slate-50/70 p-5 sm:p-7 lg:border-l lg:border-t-0 lg:p-8">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Source detail</p>
                      {selectedFact ? <><h3 className="mt-2 text-lg font-semibold text-slate-950">{selectedFact.label}</h3><p className="mt-3 text-sm leading-6 text-slate-700">{selectedFact.value}</p><p className="mt-5 text-xs font-semibold text-slate-500">{selectedFact.filename} · page {selectedFact.page_number} · {selectedFact.confidence} confidence</p><div className="mt-3 border-l-2 border-blue-300 bg-blue-50/60 px-4 py-3"><p className="text-sm leading-6 text-slate-700">{selectedFact.excerpt}</p></div></> : <p className="mt-4 text-sm leading-6 text-slate-600">Select an extracted fact to see its source excerpt.</p>}
                    </aside>
                  </div>
                ) : null}

                {evidenceMode === "documents" ? (
                  <div className="grid min-h-0 flex-1 lg:grid-cols-[minmax(260px,0.65fr)_minmax(0,1.35fr)]">
                    <aside className="min-h-0 border-b border-slate-200 bg-slate-50/70 p-5 sm:p-7 lg:border-b-0 lg:border-r lg:p-8">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Uploaded documents</p>
                      <div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">
                        {documents.map((document) => <button key={document.id} type="button" onClick={() => setSelectedDocumentId(document.id)} className={["w-full px-2 py-3 text-left transition-colors", selectedDocument?.id === document.id ? "bg-blue-50" : "hover:bg-white"].join(" ")}><p className="truncate text-sm font-semibold text-slate-900">{document.filename}</p><p className="mt-1 text-xs capitalize text-slate-500">{document.status} · {formatBytes(document.file_size)}</p></button>)}
                      </div>
                      {!isLoadingDocuments && documents.length === 0 ? <p className="mt-5 text-sm leading-6 text-slate-600">No supporting documents were attached to this assessment.</p> : null}
                    </aside>
                    <div className="min-h-0 p-5 sm:p-7 lg:p-8">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Secure document preview</p>
                      {selectedDocument ? <><h2 className="mt-2 break-words text-2xl font-semibold tracking-tight text-slate-950">{selectedDocument.filename}</h2><p className="mt-3 max-w-xl text-sm leading-6 text-slate-600">This PDF stays encrypted at rest and is decrypted only in this authenticated browser response.</p><div className="mt-6 grid max-w-xl grid-cols-2 border-y border-slate-200"><div className="py-3"><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Processing</p><p className="mt-1 text-sm font-semibold capitalize text-slate-900">{selectedDocument.status}</p></div><div className="border-l border-slate-200 py-3 pl-4"><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Size</p><p className="mt-1 text-sm font-semibold text-slate-900">{formatBytes(selectedDocument.file_size)}</p></div></div><button type="button" onClick={() => void openDocumentPreview(selectedDocument)} disabled={isPreviewLoading} className="mt-6 border border-blue-700 bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-800 disabled:cursor-wait disabled:bg-blue-400">{isPreviewLoading ? "Preparing preview..." : "Open document"}</button>{previewError ? <p className="mt-3 text-sm text-red-700">{previewError}</p> : null}</> : <p className="mt-6 text-sm leading-6 text-slate-600">Select an uploaded document to review its secure preview.</p>}
                      {documentError ? <p className="mt-4 text-sm text-red-700">{documentError}</p> : null}
                      {documentError ? <button type="button" onClick={() => setDocumentLoadAttempt((attempt) => attempt + 1)} className="mt-3 text-sm font-semibold text-blue-700 hover:text-blue-900">Retry document details</button> : null}
                    </div>
                  </div>
                ) : null}
              </section>
            ) : null}

            {activeTab === "analysis" ? (
              <section id="result-panel-analysis" role="tabpanel" aria-labelledby="result-tab-analysis" className="flex h-full min-h-0 flex-col">
                <div className="flex min-h-14 items-center justify-between gap-3 border-b border-slate-200 px-5 sm:px-7 lg:px-8">
                  <div className="flex gap-1" aria-label="Analysis view">
                    {(["fit", "dimensions", "research"] as AnalysisMode[]).map((mode) => (
                      <button key={mode} type="button" onClick={() => setAnalysisMode(mode)} className={[
                        "px-3 py-2 text-sm font-semibold capitalize transition-colors",
                        analysisMode === mode ? "text-blue-700" : "text-slate-500 hover:text-slate-900",
                      ].join(" ")}>{mode}</button>
                    ))}
                  </div>
                  <button type="button" onClick={() => setDialogContent("metadata")} className="text-sm font-semibold text-blue-700 hover:text-blue-900">Configuration</button>
                </div>

                {analysisMode === "fit" ? (
                  <div className="grid min-h-0 flex-1 overflow-y-auto lg:grid-cols-[minmax(0,1.2fr)_minmax(260px,0.8fr)] lg:overflow-hidden">
                    <div className="min-h-0 p-5 sm:p-7 lg:overflow-y-auto lg:p-8">
                      <DecisionDriverChart dimensions={result.comparison_series.dimensions} project={result.comparison_series.project} agile={result.comparison_series.agile} traditional={result.comparison_series.traditional} />
                      <div className="mt-7 border-t border-slate-200 pt-5">
                        <button
                          type="button"
                          aria-expanded={profileMapOpen}
                          aria-controls="project-profile-map"
                          onClick={() => setProfileMapOpen((current) => !current)}
                          className="flex w-full items-center justify-between gap-4 text-left text-sm font-semibold text-blue-700 transition-colors hover:text-blue-900 active:translate-y-px"
                        >
                          <span>{profileMapOpen ? "Hide" : "Explore"} project profile map</span>
                          <span className="font-mono text-xs text-slate-500">{profileMapOpen ? "−" : "+"}</span>
                        </button>
                        <p className="mt-1 text-sm leading-6 text-slate-600">Use the radar view to see the overall pattern across all decision signals.</p>
                        {profileMapOpen ? <div id="project-profile-map" className="mt-5"><RadarComparisonChart dimensions={result.comparison_series.dimensions} project={result.comparison_series.project} agile={result.comparison_series.agile} traditional={result.comparison_series.traditional} /></div> : null}
                      </div>
                    </div>
                    <div className="border-t border-slate-200 bg-slate-50/70 p-5 sm:p-7 lg:overflow-y-auto lg:border-l lg:border-t-0 lg:p-8">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Reading this chart</p>
                      <div className="mt-4 divide-y divide-slate-200 border-y border-slate-200 text-sm leading-6 text-slate-700">
                        <p className="py-3.5">Each bar compares the project signal with the active Agile and Traditional reference profiles.</p>
                        <p className="py-3.5">A longer bar means a clearer relative fit for that signal. It does not mean the signal is more important than the configured scoring weight.</p>
                        <p className="py-3.5">Open the project profile map for the three-value comparison behind every signal.</p>
                      </div>
                      <button type="button" onClick={() => setAnalysisMode("dimensions")} className="mt-5 text-sm font-semibold text-blue-700 transition-colors hover:text-blue-900 active:translate-y-px">Review exact signal scores</button>
                    </div>
                  </div>
                ) : null}

                {analysisMode === "dimensions" ? (
                  <div className="grid min-h-0 flex-1 gap-x-7 gap-y-0 p-5 sm:grid-cols-2 sm:p-7 lg:grid-cols-3 lg:p-8">
                    {result.comparison_series.dimensions.map((dimension, index) => {
                      const projectScore = result.comparison_series.project[index] ?? 0;
                      const agileGap = Math.abs(projectScore - (result.comparison_series.agile[index] ?? 0));
                      const traditionalGap = Math.abs(projectScore - (result.comparison_series.traditional[index] ?? 0));
                      const closer = agileGap <= traditionalGap ? "Agile" : "Traditional";
                      return <div key={dimension} className="border-t border-slate-200 py-3.5"><div className="flex items-start justify-between gap-3"><p className="text-sm font-semibold text-slate-800">{formatLabel(dimension)}</p><span className="text-xs font-semibold text-blue-700">{closer}</span></div><p className="mt-2 font-mono text-sm text-slate-600">{projectScore.toFixed(2)} / 5</p></div>;
                    })}
                  </div>
                ) : null}

                {analysisMode === "research" ? (
                  <div className="grid min-h-0 flex-1 lg:grid-cols-[minmax(0,1.1fr)_minmax(280px,0.9fr)]">
                    <div className="p-5 sm:p-7 lg:p-8"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Hypothesis evidence</p><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{Object.entries(report.hypothesis_evidence).map(([key, evidence]) => <div key={key} className="grid grid-cols-[42px_minmax(0,1fr)_56px] gap-3 py-3"><span className="font-mono text-xs font-semibold text-blue-700">{key}</span><span className="text-sm leading-5 text-slate-700">{evidence.label}</span><span className="font-mono text-xs font-semibold text-slate-600">{evidence.score.toFixed(2)}</span></div>)}</div></div>
                    <div className="border-t border-slate-200 bg-slate-50/70 p-5 sm:p-7 lg:border-l lg:border-t-0 lg:p-8"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Research boundary</p><p className="mt-4 text-sm leading-6 text-slate-700">{strategy.research_boundary_note}</p><p className="mt-5 text-sm leading-6 text-slate-600">{report.limitations[0]}</p></div>
                  </div>
                ) : null}
              </section>
            ) : null}
          </div>
        </section>

        <footer className="flex min-h-10 items-center justify-between border-t border-slate-200 bg-[#f6f8fc] px-4 text-xs text-slate-500 sm:px-6 lg:px-8 xl:px-12">
          <span>Rules v{result.rules_version} · Questionnaire v{result.questionnaire_version}</span>
          <span className="hidden sm:inline">{new Date(result.created_at).toLocaleString()}</span>
        </footer>
      </div>

      {dialogContent ? (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/35 p-4" role="presentation">
          <section role="dialog" aria-modal="true" aria-label="Result detail" className="w-full max-w-2xl border border-slate-200 bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4"><p className="text-base font-semibold text-slate-950">{dialogContent === "trace" ? "Evidence processing trace" : dialogContent === "metadata" ? "Configuration trace" : "Cited excerpt"}</p><button type="button" onClick={() => setDialogContent(null)} aria-label="Close detail" className="p-1.5 text-slate-500 hover:text-slate-900"><X size={18} /></button></div>
            <div className="p-5">
              {dialogContent === "trace" ? <div className="divide-y divide-slate-200 border-y border-slate-200">{result.ai_demo_trace.slice(0, 7).map((step, index) => <div key={`${step.stage}-${index}`} className="grid gap-2 py-3 sm:grid-cols-[minmax(0,1fr)_76px]"><div><p className="text-sm font-semibold text-slate-900">{step.label}</p><p className="mt-1 text-sm leading-5 text-slate-600">{step.detail}</p></div><span className="font-mono text-xs text-slate-500">{step.duration_ms} ms</span></div>)}</div> : null}
              {dialogContent === "metadata" ? <div className="space-y-3 text-sm text-slate-700"><p>Rules version: {result.rules_version}</p><p>Questionnaire version: {result.questionnaire_version}</p><p>Created: {new Date(result.created_at).toLocaleString()}</p></div> : null}
              {dialogContent === "excerpt" && selectedCitation ? <div><p className="text-xs font-semibold text-slate-500">{selectedCitation.filename} · page {selectedCitation.page_number}</p><p className="mt-4 text-sm leading-6 text-slate-700">{selectedCitation.excerpt}</p></div> : null}
            </div>
          </section>
        </div>
      ) : null}

      {previewUrl ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/55 p-3 sm:p-6" role="presentation">
          <section role="dialog" aria-modal="true" aria-label="Secure document preview" className="flex h-full w-full max-w-6xl flex-col border border-slate-300 bg-white shadow-2xl">
            <div className="flex min-h-14 items-center justify-between gap-4 border-b border-slate-200 px-4 sm:px-5">
              <p className="truncate text-sm font-semibold text-slate-900">{previewTitle}</p>
              <button type="button" onClick={closePreview} aria-label="Close document preview" className="shrink-0 p-1.5 text-slate-500 hover:text-slate-900"><X size={18} /></button>
            </div>
            <object data={previewUrl} type="application/pdf" className="min-h-0 flex-1 bg-slate-100" aria-label={previewTitle}>
              <p className="p-5 text-sm text-slate-600">This browser cannot render the PDF preview.</p>
            </object>
          </section>
        </div>
      ) : null}
    </main>
  );
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function SignalRow({ icon: Icon, label, body }: { icon: typeof Warning; label: string; body: string }) {
  return <div className="py-3.5"><p className="flex items-center gap-2 text-sm font-semibold text-slate-900"><Icon size={17} weight="bold" className="text-blue-700" aria-hidden="true" />{label}</p><p className="mt-2 text-sm leading-5 text-slate-600">{body}</p></div>;
}
