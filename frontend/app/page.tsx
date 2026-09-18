"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle } from "@phosphor-icons/react";
import { useCallback, useEffect, useRef, useState } from "react";
import BackButton from "@/components/BackButton";
import AssessmentReview from "@/components/AssessmentReview";
import DocumentProcessingAside from "@/components/DocumentProcessingAside";
import DocumentProcessingWait from "@/components/DocumentProcessingWait";
import DocumentUploadScreen from "@/components/DocumentUploadScreen";
import EvidenceAnswerReview from "@/components/EvidenceAnswerReview";
import LikertScreen from "@/components/LikertScreen";
import PillSelectQuestion from "@/components/PillSelectQuestion";
import ProgressBar from "@/components/ProgressBar";
import QuestionnaireShell from "@/components/QuestionnaireShell";
import TextQuestion from "@/components/TextQuestion";
import {
  createAssessment,
  confirmEvidenceAnswer,
  createDraft,
  getEvidenceAnswers,
  getActiveQuestionnaire,
  getDraftStatus,
  DEFAULT_LIKERT_SCALE_LABELS,
  trackAssessmentEvent,
  type AssessmentCreateResponse,
  type EvidenceAnswerData,
  type QuestionnairePayload,
  type DraftStatusResponse,
} from "@/lib/api";
import ResultWorkspace from "@/components/results/ResultWorkspace";
import { PUBLIC_PAGE_TITLES } from "@/lib/pageMeta";

type State = {
  screen: number;
  profile: Record<string, string>;
  profileOtherInputs: Record<string, string>;
  answers: Record<string, number>;
  result: AssessmentCreateResponse | null;
  draftId: string | null;
  submitting: boolean;
  submitError: string | null;
  flowNotice: string | null;
  reviewingAnswer: boolean;
  trackedQuestionIds: string[];
  evidenceAnswers: EvidenceAnswerData[];
};

const INITIAL_STATE: State = {
  screen: 0,
  profile: {},
  profileOtherInputs: {},
  answers: {},
  result: null,
  draftId: null,
  submitting: false,
  submitError: null,
  flowNotice: null,
  reviewingAnswer: false,
  trackedQuestionIds: [],
  evidenceAnswers: [],
};

const CONSTRUCT_LABELS: Record<"FLEXIBILITY" | "PERFORMANCE" | "STRICTNESS", string> = {
  FLEXIBILITY: "Adaptation and iterative readiness",
  PERFORMANCE: "Delivery constraints",
  STRICTNESS: "Assurance and dependency complexity",
};

const DEFAULT_QUESTIONNAIRE: QuestionnairePayload = {
  profile_questions: [
    { question_id: "Q1", kind: "text", profile_key: "name", prompt: "What's your name?", placeholder: "Your full name" },
    { question_id: "Q2", kind: "pill", profile_key: "role", prompt: "What is your role?", options: ["Project Manager", "Software Developer", "System Architect", "IS Practitioner", "Executive", "Other"] },
    { question_id: "Q3", kind: "text", profile_key: "company", prompt: "What's your company name?", placeholder: "Company or organization name" },
    { question_id: "Q4", kind: "pill", profile_key: "industry", prompt: "What industry are you in?", options: ["Government", "Banking & Finance", "Healthcare", "Technology", "Telecom", "Education", "Retail", "Other"] },
    { question_id: "Q5", kind: "pill", profile_key: "orgSize", prompt: "How large is your organization?", options: ["1-10", "11-50", "51-200", "201-1,000", "1,000+"] },
    { question_id: "Q6", kind: "text", profile_key: "projectName", prompt: "What's the name of your project?", placeholder: "Project name" },
    { question_id: "Q7", kind: "pill", profile_key: "projectType", prompt: "What type of project is this?", options: ["New System", "System Integration", "Upgrade & Migration", "Maintenance", "Other"] },
    { question_id: "Q8", kind: "pill", profile_key: "duration", prompt: "What is the expected project duration?", options: ["< 3 months", "3-6 months", "6-12 months", "1-2 years", "2+ years"] },
    { question_id: "Q9", kind: "pill", profile_key: "teamSize", prompt: "How large is your project team?", options: ["1-5", "6-15", "16-30", "30+"] },
    { question_id: "Q10", kind: "pill", profile_key: "budget", prompt: "What is the approximate budget range?", options: ["< $10K", "$10K-$50K", "$50K-$200K", "$200K-$1M", "$1M+", "Prefer not to say"] },
  ],
  likert_questions: [
    { question_id: "Q11", construct: "FLEXIBILITY", prompt: "How much are requirements expected to change after development begins?", scale_labels: ["Stable", "Minor change", "Occasional change", "Frequent change", "Constant or substantial change"] },
    { question_id: "Q12", construct: "FLEXIBILITY", prompt: "How much uncertainty exists about the final solution and its acceptance criteria?", scale_labels: ["Fully defined", "Mostly defined", "Partly defined", "Significant uncertainty", "Substantial discovery required"] },
    { question_id: "Q13", construct: "FLEXIBILITY", prompt: "How often can an authorized stakeholder review work and make priority decisions?", scale_labels: ["Major milestones only", "Monthly", "Every 2–4 weeks", "Weekly", "Whenever needed"] },
    { question_id: "Q14", construct: "FLEXIBILITY", prompt: "How capable is the team of planning, building, testing, and reviewing work in short cycles?", scale_labels: ["No capability", "Limited", "Developing", "Capable", "Highly experienced"] },
    { question_id: "Q15", construct: "PERFORMANCE", prompt: "How fixed is the delivery date because of contractual, legal, launch, or external commitments?", scale_labels: ["Flexible", "Target only", "Important with flexibility", "Externally committed", "Immovable"] },
    { question_id: "Q16", construct: "PERFORMANCE", prompt: "How fixed is the project budget or funding ceiling?", scale_labels: ["Flexible", "Broad tolerance", "Moderate constraint", "Tight constraint", "No overrun permitted"] },
    { question_id: "Q17", construct: "PERFORMANCE", prompt: "How much formal approval is required before the delivery plan can be changed?", scale_labels: ["Team discretion", "Lightweight approval", "Manager approval", "Multiple approvals", "Contractual or board approval"] },
    { question_id: "Q18", construct: "STRICTNESS", prompt: "What level of regulatory, legal, or audit obligation applies?", scale_labels: ["None", "Low", "Moderate", "High", "Extensive mandatory obligations"] },
    { question_id: "Q19", construct: "STRICTNESS", prompt: "What is the highest credible consequence if the system fails or is compromised?", scale_labels: ["Low and reversible", "Limited", "Moderate", "Serious", "Severe or legally significant"] },
    { question_id: "Q20", construct: "STRICTNESS", prompt: "How much controlled documentation and end-to-end traceability is required?", scale_labels: ["Working notes", "Basic", "Standard", "Detailed", "Complete audit-grade traceability"] },
    { question_id: "Q21", construct: "STRICTNESS", prompt: "How dependent is delivery on external vendors, legacy systems, or interfaces outside the team's control?", scale_labels: ["Self-contained", "Few dependencies", "Moderate", "Several critical dependencies", "Many critical external dependencies"] },
    { question_id: "Q22", construct: "STRICTNESS", prompt: "How much coordination and sequencing is required across teams or organizations?", scale_labels: ["One small team", "Few interactions", "Multiple teams", "Distributed sequencing", "Tightly coupled multi-organization delivery"] },
  ],
  document_questions: [],
};

export default function Home() {
  const [state, setState] = useState<State>(INITIAL_STATE);
  const [questionnaire, setQuestionnaire] = useState<QuestionnairePayload>(DEFAULT_QUESTIONNAIRE);
  const [visibleTraceSteps, setVisibleTraceSteps] = useState(0);
  const [assessmentSessionId, setAssessmentSessionId] = useState<string | null>(null);
  const [documentStatus, setDocumentStatus] = useState<DraftStatusResponse | null>(null);
  const [documentStatusError, setDocumentStatusError] = useState<string | null>(null);
  const isLoadingEvidenceRef = useRef(false);

  useEffect(() => {
    void getActiveQuestionnaire()
      .then((data) => setQuestionnaire(data.payload))
      .catch(() => setQuestionnaire(DEFAULT_QUESTIONNAIRE));
  }, []);

  useEffect(() => {
    if (!state.result) {
      setVisibleTraceSteps(0);
      return;
    }
    if (visibleTraceSteps >= state.result.ai_demo_trace.length) {
      return;
    }
    const timer = window.setTimeout(() => {
      setVisibleTraceSteps((previous) => previous + 1);
    }, 900);
    return () => window.clearTimeout(timer);
  }, [state.result, visibleTraceSteps]);

  const profileCount = questionnaire.profile_questions.length;
  const likertCount = questionnaire.likert_questions.length;
  const questionCount = profileCount + likertCount;
  const profileStartScreen = 1;
  const profileEndScreen = profileStartScreen + profileCount - 1;
  const uploadScreen = profileEndScreen + 1;
  const likertStartScreen = uploadScreen + 1;
  const likertEndScreen = likertStartScreen + likertCount - 1;
  const documentWaitScreen = likertEndScreen + 1;
  const evidenceReviewScreen = documentWaitScreen + 1;
  const reviewScreen = evidenceReviewScreen + 1;
  const resultScreen = reviewScreen + 1;
  useEffect(() => {
    if (state.result || state.screen === resultScreen) {
      document.title = PUBLIC_PAGE_TITLES.result;
      return;
    }
    document.title = state.screen === 0 ? PUBLIC_PAGE_TITLES.landing : PUBLIC_PAGE_TITLES.progress;
  }, [resultScreen, state.result, state.screen]);

  const goNext = () => {
    setState((previous) => ({
      ...previous,
      screen: Math.min(previous.screen + 1, resultScreen),
    }));
  };

  const goBack = () => {
    setState((previous) => ({
      ...previous,
      screen:
        previous.screen === likertStartScreen
          ? uploadScreen
          : previous.screen === documentWaitScreen || previous.screen === evidenceReviewScreen || previous.screen === reviewScreen
            ? likertEndScreen
          : Math.max(previous.screen - 1, 0),
    }));
  };

  const refreshDocumentStatus = useCallback(async () => {
    if (!state.draftId) return;
    try {
      const nextStatus = await getDraftStatus(state.draftId);
      setDocumentStatus(nextStatus);
      setDocumentStatusError(null);
    } catch (error) {
      setDocumentStatusError(error instanceof Error ? error.message : "Unable to refresh document processing status.");
    }
  }, [state.draftId]);

  useEffect(() => {
    if (documentStatus?.status !== "processing") return;
    const timer = window.setInterval(() => void refreshDocumentStatus(), 1800);
    return () => window.clearInterval(timer);
  }, [documentStatus?.status, refreshDocumentStatus]);

  const getOrCreateAssessmentSessionId = () => {
    if (assessmentSessionId) {
      return assessmentSessionId;
    }
    const nextSessionId =
      globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    setAssessmentSessionId(nextSessionId);
    return nextSessionId;
  };

  const trackQuestionProgress = (questionKey: string, questionIndex: number) => {
    const sessionId = getOrCreateAssessmentSessionId();
    void trackAssessmentEvent({
      session_id: sessionId,
      event: "question_answered",
      question_key: questionKey,
      question_index: questionIndex,
    }).catch(() => undefined);
  };

  const trackQuestionOnce = (questionKey: string, questionIndex: number) => {
    if (state.trackedQuestionIds.includes(questionKey)) {
      return;
    }
    setState((previous) => ({
      ...previous,
      trackedQuestionIds: previous.trackedQuestionIds.includes(questionKey)
        ? previous.trackedQuestionIds
        : [...previous.trackedQuestionIds, questionKey],
    }));
    trackQuestionProgress(questionKey, questionIndex);
  };

  const beginAssessment = async () => {
    const sessionId = getOrCreateAssessmentSessionId();
    void trackAssessmentEvent({ session_id: sessionId, event: "opened" }).catch(() => undefined);
    setState((previous) => ({ ...previous, submitting: true, submitError: null }));
    try {
      const draft = await createDraft(sessionId);
      setState((previous) => ({ ...previous, submitting: false, draftId: draft.draft_id, screen: profileStartScreen }));
    } catch (error) {
      setState((previous) => ({
        ...previous,
        submitting: false,
        flowNotice: error instanceof Error ? "Document evidence is unavailable. Continue with the manual assessment." : null,
        screen: profileStartScreen,
      }));
    }
  };

  const selectProfileAnswer = (key: string, value: string, advance: boolean, otherValue?: string) => {
    const returnToReview = state.reviewingAnswer;
    if (advance && profileQuestion) {
      trackQuestionOnce(profileQuestion.question_id, profileIndex + 1);
    }
    setState((previous) => ({
      ...previous,
      profile: { ...previous.profile, [key]: value },
      profileOtherInputs:
        otherValue && otherValue.trim()
          ? { ...previous.profileOtherInputs, [key]: otherValue }
          : Object.fromEntries(Object.entries(previous.profileOtherInputs).filter(([entryKey]) => entryKey !== key)),
      screen: advance
        ? returnToReview
          ? reviewScreen
          : Math.min(previous.screen + 1, resultScreen)
        : previous.screen,
      reviewingAnswer: advance && returnToReview ? false : previous.reviewingAnswer,
    }));
  };

  const submitAssessment = async (
    answersOverride?: Record<string, number>,
    draftIdOverride?: string | null,
    flowNotice?: string | null
  ) => {
    const resolvedAnswers = answersOverride ?? state.answers;
    const resolvedDraftId = draftIdOverride ?? state.draftId;
    const unansweredIndex = questionnaire.likert_questions.findIndex(
      (question) => resolvedAnswers[question.question_id] === undefined
    );
    if (unansweredIndex >= 0) {
      setState((previous) => ({
        ...previous,
        screen: likertStartScreen + unansweredIndex,
        submitting: false,
        submitError: "Please answer every methodology question before calculating the recommendation.",
      }));
      return;
    }
    setState((previous) => ({
      ...previous,
      submitting: true,
      submitError: null,
      flowNotice: flowNotice ?? previous.flowNotice,
      screen: resultScreen,
    }));
    try {
      const response = await createAssessment({
        profile: {
          name: state.profile.name ?? "",
          role: state.profile.role ?? "",
          company: state.profile.company ?? "",
          industry: state.profile.industry ?? "",
          org_size: state.profile.orgSize ?? "",
          project_name: state.profile.projectName ?? "",
          project_type: state.profile.projectType ?? "",
          duration: state.profile.duration ?? "",
          team_size: state.profile.teamSize ?? "",
          budget: state.profile.budget ?? "",
        },
        answers: questionnaire.likert_questions.map((question) => ({
          question_key: question.question_id,
          construct: question.construct,
          value: resolvedAnswers[question.question_id]!,
        })),
        profile_other_inputs:
          Object.keys(state.profileOtherInputs).length > 0 ? state.profileOtherInputs : undefined,
        draft_id: resolvedDraftId,
        session_id: assessmentSessionId,
      });
      setVisibleTraceSteps(0);
      setState((previous) => ({ ...previous, result: response, submitting: false }));
    } catch (error: unknown) {
      setState((previous) => ({
        ...previous,
        submitting: false,
        submitError: error instanceof Error ? error.message : "Failed to submit assessment.",
      }));
    }
  };

  const selectLikertAnswer = async (value: number) => {
    const likertIndex = state.screen - likertStartScreen;
    const currentLikert = questionnaire.likert_questions[likertIndex];
    if (!currentLikert) {
      return;
    }

    const isLastLikert = likertIndex === likertCount - 1;
    const returnToReview = state.reviewingAnswer;
    const nextAnswers = { ...state.answers, [currentLikert.question_id]: value };
    const nextScreen = returnToReview
      ? reviewScreen
      : isLastLikert
        ? documentStatus?.status === "ready" || documentStatus?.status === "processing"
            ? documentWaitScreen
            : reviewScreen
        : Math.min(state.screen + 1, resultScreen);
    trackQuestionOnce(currentLikert.question_id, profileCount + likertIndex + 1);

    setState((previous) => ({
      ...previous,
      answers: nextAnswers,
      submitting: false,
      submitError: null,
      screen: nextScreen,
      reviewingAnswer: returnToReview ? false : previous.reviewingAnswer,
    }));

    if (!isLastLikert || returnToReview || documentStatus?.status !== "ready") {
      return;
    }
    void loadEvidenceReview();
  };

  const submitTextProfileAnswer = () => {
    if (!profileQuestion) {
      return;
    }
    const value = (state.profile[profileQuestion.profile_key] ?? "").trim();
    if (!value) {
      return;
    }
    trackQuestionOnce(profileQuestion.question_id, profileIndex + 1);
    if (state.reviewingAnswer) {
      setState((previous) => ({ ...previous, screen: reviewScreen, reviewingAnswer: false }));
      return;
    }
    goNext();
  };

  const loadEvidenceReview = useCallback(async () => {
    if (!state.draftId) {
      setState((previous) => ({ ...previous, screen: likertStartScreen }));
      return;
    }
    if (isLoadingEvidenceRef.current) return;
    isLoadingEvidenceRef.current = true;
    setState((previous) => ({ ...previous, submitting: true, submitError: null }));
    try {
      const evidenceAnswers = await getEvidenceAnswers(state.draftId);
      setState((previous) => ({ ...previous, evidenceAnswers, submitting: false, screen: evidenceReviewScreen }));
    } catch (error) {
      setState((previous) => ({
        ...previous,
        submitting: false,
        submitError: error instanceof Error ? error.message : "Unable to load extracted evidence.",
      }));
    } finally {
      isLoadingEvidenceRef.current = false;
    }
  }, [evidenceReviewScreen, likertStartScreen, state.draftId]);

  useEffect(() => {
    if (state.screen !== documentWaitScreen) return;
    if (documentStatus?.status === "ready") {
      void loadEvidenceReview();
      return;
    }
    if (documentStatus?.status === "failed") {
      setState((previous) => ({ ...previous, screen: reviewScreen }));
    }
  }, [documentStatus?.status, documentWaitScreen, loadEvidenceReview, reviewScreen, state.screen]);

  const confirmDocumentEvidence = async (confirmedQuestionKeys: string[]) => {
    if (!state.draftId) {
      setState((previous) => ({ ...previous, screen: likertStartScreen }));
      return;
    }
    const documentEvidence = state.evidenceAnswers.filter((item) => item.construct && item.answer_type === "likert");
    await Promise.all(
      documentEvidence.map((item) =>
        confirmEvidenceAnswer(
          state.draftId as string,
          item.question_key,
          confirmedQuestionKeys.includes(item.question_key) ? "confirm" : "omit"
        )
      )
    );
    setState((previous) => ({ ...previous, screen: reviewScreen }));
  };

  const resetAssessment = () => {
    setVisibleTraceSteps(0);
    setAssessmentSessionId(null);
    setDocumentStatus(null);
    setDocumentStatusError(null);
    setState(INITIAL_STATE);
  };

  const profileIndex = state.screen - profileStartScreen;
  const likertIndex = state.screen - likertStartScreen;
  const profileQuestion =
    state.screen >= profileStartScreen && state.screen <= profileEndScreen
      ? questionnaire.profile_questions[profileIndex]
      : null;
  const likertQuestion =
    state.screen >= likertStartScreen && state.screen <= likertEndScreen
      ? questionnaire.likert_questions[likertIndex]
      : null;
  const traceSteps = state.result?.ai_demo_trace ?? [];
  const displayedTraceSteps = traceSteps.slice(0, visibleTraceSteps);
  const isThinkingLoopActive = Boolean(state.result && visibleTraceSteps < traceSteps.length);
  const questionEyebrow =
    state.screen >= profileStartScreen && state.screen <= profileEndScreen
      ? "Project context"
      : state.screen >= likertStartScreen && state.screen <= likertEndScreen
        ? "Method fit signals"
        : "Reference documents";
  const questionHelper = profileQuestion
    ? profileQuestion.kind === "text"
      ? "Use the wording you would want to see in the final assessment summary."
      : "Pick the closest option. You can still go back before the recommendation is generated."
    : likertQuestion
      ? "Choose the score that best matches the current project reality."
      : "";
  const isProfileStage = state.screen >= profileStartScreen && state.screen <= profileEndScreen;
  const isMethodStage = state.screen >= likertStartScreen && state.screen <= likertEndScreen;
  const currentQuestionNumber = isProfileStage
    ? profileIndex + 1
    : isMethodStage
      ? profileCount + likertIndex + 1
      : 0;
  const journeyStages = [
    {
      label: "Project context",
      detail: `${profileCount} questions`,
      status: state.screen === 0 || isProfileStage ? "active" : state.screen > profileEndScreen ? "complete" : "upcoming",
    },
    {
      label: "Evidence",
      detail: "Optional documents",
      status: state.screen === uploadScreen || state.screen === documentWaitScreen || state.screen === evidenceReviewScreen ? "active" : state.screen > evidenceReviewScreen ? "complete" : "upcoming",
    },
    {
      label: "Method signals",
      detail: `${likertCount} questions`,
      status: isMethodStage ? "active" : state.screen > likertEndScreen ? "complete" : "upcoming",
    },
    {
      label: "Review",
      detail: "Check your brief",
      status: state.screen === reviewScreen ? "active" : state.screen > reviewScreen ? "complete" : "upcoming",
    },
    {
      label: "Recommendation",
      detail: "Review the result",
      status: state.screen === resultScreen ? "active" : "upcoming",
    },
  ];
  const renderJourneyStages = () => (
    <>
      <nav aria-label="Assessment progress">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-600">Assessment path</p>
        <ol className="mt-5 grid grid-cols-2 gap-x-4 gap-y-5 lg:block lg:space-y-5">
        {journeyStages.map((stage) => (
          <li key={stage.label} className="flex items-start gap-3">
            <span
              className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                stage.status === "complete"
                  ? "bg-blue-700 text-white"
                  : stage.status === "active"
                    ? "bg-blue-100 text-blue-700 ring-4 ring-blue-50"
                    : "bg-slate-200 text-slate-500"
              }`}
            >{stage.status === "complete" ? "✓" : journeyStages.indexOf(stage) + 1}</span>
            <div>
              <p
                className={`text-sm font-semibold leading-5 ${
                  stage.status === "upcoming" ? "text-slate-600" : "text-slate-900"
                }`}
              >
                {stage.label}
              </p>
              <p className="text-xs text-slate-600">{stage.detail}</p>
            </div>
          </li>
        ))}
        </ol>
      </nav>
      {documentStatus ? <DocumentProcessingAside status={documentStatus} refreshError={documentStatusError} /> : null}
    </>
  );

  const shouldUseQuestionnaireShell =
    state.screen === 0 ||
    (state.screen >= profileStartScreen && state.screen <= likertEndScreen) ||
    state.screen === reviewScreen ||
    state.screen === uploadScreen ||
    state.screen === documentWaitScreen ||
    state.screen === evidenceReviewScreen ||
    (state.screen === resultScreen && (!state.result || isThinkingLoopActive));

  let shellHeader = null;
  let shellMain = null;
  let shellAside = null;
  let shellCenterMain = false;

  if (state.screen === 0) {
    shellHeader = (
      <span className="text-sm font-medium text-slate-600">{questionCount} questions · about 3 minutes</span>
    );
    shellMain = (
      <section className="border-y border-slate-200 bg-white px-5 py-10 sm:border sm:px-10 sm:py-14">
        <div className="border-l-2 border-blue-700 pl-5 sm:pl-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Assessment brief</p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">Find the delivery method that fits this project.</h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">Capture the project context, rate its delivery conditions, and review the resulting recommendation before it is finalized.</p>
        </div>
        <div className="mt-10 divide-y divide-slate-200 border-y border-slate-200">
          {[
            ["01", "Project context", "The team, organisation, scope, and delivery constraints."],
            ["02", "Supporting documents", "Optional project evidence to enrich the assessment."],
            ["03", "Method signals", "A short set of statements about change, control, and pace."],
            ["04", "Decision brief", "A recommendation with rationale and document evidence."],
          ].map(([number, title, detail]) => (
            <div key={number} className="grid gap-2 py-4 sm:grid-cols-[48px_180px_minmax(0,1fr)] sm:items-start">
              <span className="font-mono text-sm font-semibold text-blue-700">{number}</span>
              <p className="text-sm font-semibold text-slate-900">{title}</p>
              <p className="text-sm leading-6 text-slate-600">{detail}</p>
            </div>
          ))}
        </div>
        <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
            <button
              type="button"
              onClick={beginAssessment}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-blue-700 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-800 active:translate-y-px"
            >
              Begin assessment
            </button>
          <p className="text-sm text-slate-500">You can amend individual answers during review.</p>
        </div>
      </section>
    );
    shellAside = renderJourneyStages();
  } else if (isProfileStage || isMethodStage) {
    shellCenterMain = true;
    shellHeader = (
      <div className="flex items-center gap-2">
        <BackButton onClick={goBack} />
        <ProgressBar currentScreen={currentQuestionNumber} totalQuestions={questionCount} profileQuestions={profileCount} />
      </div>
    );
    shellMain = (
      <>
        {profileQuestion?.kind === "text" ? (
          <TextQuestion
            key={`text-${profileQuestion.question_id}`}
            question={profileQuestion.prompt}
            placeholder={profileQuestion.placeholder ?? ""}
            value={state.profile[profileQuestion.profile_key] ?? ""}
            eyebrow={questionEyebrow}
            helper={questionHelper}
            onChange={(value) => selectProfileAnswer(profileQuestion.profile_key, value, false)}
            onSubmit={submitTextProfileAnswer}
          />
        ) : null}

        {profileQuestion?.kind === "pill" ? (
          <PillSelectQuestion
            key={`pill-${profileQuestion.question_id}`}
            question={profileQuestion.prompt}
            options={profileQuestion.options ?? []}
            initialValue={state.profile[profileQuestion.profile_key] || undefined}
            initialOtherValue={state.profileOtherInputs[profileQuestion.profile_key] ?? ""}
            eyebrow={questionEyebrow}
            helper={questionHelper}
            onOtherValueChange={(value) =>
              setState((previous) => ({
                ...previous,
                profileOtherInputs: { ...previous.profileOtherInputs, [profileQuestion.profile_key]: value },
              }))
            }
            onSelect={(value, otherValue) =>
              selectProfileAnswer(profileQuestion.profile_key, value, true, otherValue)
            }
          />
        ) : null}

        {likertQuestion ? (
          <LikertScreen
            key={`likert-${likertQuestion.question_id}`}
            construct={CONSTRUCT_LABELS[likertQuestion.construct]}
            question={likertQuestion.prompt}
            scaleLabels={likertQuestion.scale_labels ?? DEFAULT_LIKERT_SCALE_LABELS}
            helper={questionHelper}
            initialValue={state.answers[likertQuestion.question_id] ?? undefined}
            onSelect={selectLikertAnswer}
          />
        ) : null}
      </>
    );
    shellAside = renderJourneyStages();
  } else if (state.screen === reviewScreen) {
    shellHeader = <BackButton onClick={goBack} />;
    shellMain = (
      <AssessmentReview
        profileQuestions={questionnaire.profile_questions}
        likertQuestions={questionnaire.likert_questions}
        profile={state.profile}
        profileOtherInputs={state.profileOtherInputs}
        answers={state.answers}
        isPreparing={state.submitting}
        onContinue={() => void submitAssessment()}
        onEditProfile={(index) => setState((previous) => ({ ...previous, screen: profileStartScreen + index, reviewingAnswer: true }))}
        onEditLikert={(index) => setState((previous) => ({ ...previous, screen: likertStartScreen + index, reviewingAnswer: true }))}
      />
    );
    shellAside = renderJourneyStages();
  } else if (state.screen === uploadScreen && state.draftId) {
    shellCenterMain = true;
    shellHeader = (
      <div className="flex items-center gap-2">
        <BackButton onClick={goBack} />
        <span className="text-sm font-medium text-slate-500">Optional supporting evidence</span>
      </div>
    );
    shellMain = (
      <DocumentUploadScreen
        draftId={state.draftId}
        onContinue={() => setState((previous) => ({ ...previous, screen: likertStartScreen }))}
        onProcessingStarted={(nextStatus) => {
          setDocumentStatus(nextStatus);
          setDocumentStatusError(null);
          setState((previous) => ({ ...previous, screen: likertStartScreen }));
        }}
        onSkip={() => setState((previous) => ({ ...previous, screen: likertStartScreen }))}
      />
    );
    shellAside = renderJourneyStages();
  } else if (state.screen === documentWaitScreen) {
    shellHeader = <BackButton onClick={goBack} />;
    shellMain = <DocumentProcessingWait status={documentStatus} refreshError={documentStatusError} />;
    shellAside = renderJourneyStages();
  } else if (state.screen === evidenceReviewScreen) {
    shellHeader = <BackButton onClick={goBack} />;
    shellMain = (
      <EvidenceAnswerReview
        answers={state.evidenceAnswers}
        onComplete={confirmDocumentEvidence}
      />
    );
    shellAside = renderJourneyStages();
  } else if (state.screen === resultScreen && (!state.result || isThinkingLoopActive)) {
    shellHeader = (
      <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
        <CheckCircle size={18} className="text-blue-700" weight="duotone" />
        {state.submitting && !state.result ? "Scoring responses" : "Building decision brief"}
      </div>
    );
    shellMain = (
      <section className="border-y border-slate-200 bg-white px-5 py-8 sm:border sm:px-10 sm:py-11">
        {state.submitting && !state.result ? (
          <div className="animate-pulse">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Decision engine</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">Calculating methodology fit</h1>
            <div className="animate-pulse space-y-4">
              <div className="mt-7 h-3 w-32 bg-blue-100" />
              <div className="h-8 max-w-xl bg-slate-100" />
              <div className="h-20 bg-slate-100" />
            </div>
          </div>
        ) : null}
        {state.flowNotice ? (
          <div className="mt-5 border-l-2 border-amber-500 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {state.flowNotice}
          </div>
        ) : null}
        {state.submitError ? (
          <div className="mt-5 border-l-2 border-rose-500 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {state.submitError}
            <div className="mt-3">
              <button
                type="button"
                onClick={() =>
                  setState((previous) => ({
                    ...previous,
                    screen: likertEndScreen,
                    submitError: null,
                  }))
                }
                className="rounded-md border border-rose-300 bg-white px-3 py-1 text-xs font-semibold text-rose-700"
              >
                Go back to last question
              </button>
            </div>
          </div>
        ) : null}
        {state.result && isThinkingLoopActive ? (
          <section className="mt-8">
            <div className="border-l-2 border-blue-700 pl-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Evidence review</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">Building the decision brief</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Each stage is processed in sequence so the assessment rationale is clear and traceable.</p>
            </div>
            <div className="mt-8 divide-y divide-slate-200 border-y border-slate-200">
              {displayedTraceSteps.map((step, index) => (
                <div key={`${step.stage}-${index}`} className="grid gap-2 py-4 sm:grid-cols-[150px_minmax(0,1fr)_auto] sm:items-start">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-slate-900">{step.label}</p>
                  </div>
                  <p className="text-sm leading-6 text-slate-600">{step.detail}</p>
                  <span className="w-fit text-xs font-semibold text-blue-700">{step.status}</span>
                </div>
              ))}
            </div>
            {visibleTraceSteps < traceSteps.length ? <p className="mt-4 text-sm font-medium text-blue-700">Preparing next stage...</p> : null}
          </section>
        ) : null}
      </section>
    );
    shellAside = renderJourneyStages();
  }

  return shouldUseQuestionnaireShell ? (
    <QuestionnaireShell
      header={shellHeader}
      main={
        <div key={state.screen} className="motion-safe:transition-opacity motion-safe:duration-150">
          {shellMain}
        </div>
      }
      aside={shellAside}
      centerMain={shellCenterMain}
      mainWidth={state.screen === evidenceReviewScreen ? "wide" : "standard"}
    />
  ) : state.screen === resultScreen && state.result ? (
    <ResultWorkspace
      result={state.result}
      draftId={state.draftId}
      questions={[
        ...questionnaire.profile_questions.map((question) => ({
          key: question.question_id,
          section: "Project context" as const,
          prompt: question.prompt,
          value:
            state.profile[question.profile_key] === "Other" && state.profileOtherInputs[question.profile_key]
              ? state.profileOtherInputs[question.profile_key]
              : state.profile[question.profile_key] ?? "Not provided",
        })),
        ...questionnaire.likert_questions.map((question) => ({
          key: question.question_id,
          section: "Method signals" as const,
          prompt: question.prompt,
          value: state.answers[question.question_id] === undefined
            ? "Not answered"
            : `${state.answers[question.question_id]} / 5 · ${(question.scale_labels ?? DEFAULT_LIKERT_SCALE_LABELS)[state.answers[question.question_id] - 1]}`,
        })),
      ]}
      name={state.profile.name ?? ""}
      onRestart={resetAssessment}
    />
  ) : (
    <main className="relative min-h-[100dvh] overflow-hidden bg-[#f6f8fc] text-slate-900">

      <AnimatePresence mode="wait">
        <motion.section
          key={state.screen}
          initial={{ x: 40, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -40, opacity: 0 }}
          transition={{ duration: 0.26, ease: "easeOut" }}
          className="absolute inset-0 flex w-full overflow-y-auto px-4 pt-10 sm:pt-12"
        >
          <div className={["mx-auto w-full", state.screen === resultScreen ? "max-w-6xl" : "max-w-xl", state.screen >= profileStartScreen && state.screen <= likertEndScreen ? "my-auto" : ""].join(" ")}>
          </div>
        </motion.section>
      </AnimatePresence>
    </main>
  );
}
