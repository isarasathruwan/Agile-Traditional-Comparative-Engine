import { expect, test, type Page, type Route } from "@playwright/test";

const questionnaire = {
  version: 3,
  title: "Method fit test questionnaire",
  payload: {
    profile_questions: [
      {
        question_id: "Q1",
        kind: "text",
        profile_key: "name",
        prompt: "What's your name?",
        placeholder: "Your full name",
      },
    ],
    likert_questions: [
      {
        question_id: "Q11",
        construct: "FLEXIBILITY",
        prompt: "How much are requirements expected to change?",
        scale_labels: ["Stable", "Minor", "Occasional", "Frequent", "Constant"],
      },
    ],
    document_questions: [],
  },
  changed_by: "test-suite",
  change_note: "Deterministic browser fixture",
  created_at: "2026-07-30T10:00:00Z",
};

const collectingStatus = {
  draft_id: "browser-draft",
  status: "collecting",
  duplicate_rejection_count: 0,
  uploads_locked: false,
  documents: [],
  processing: {
    status: "collecting",
    queued_jobs: 0,
    completed_jobs: 0,
    failed_jobs: 0,
    current_stage: "ready",
    current_stage_label: "Evidence is ready for review",
    current_document_name: null,
    processed_documents: 0,
    total_documents: 0,
    message: null,
  },
};

const failedStatus = {
  ...collectingStatus,
  status: "failed",
  uploads_locked: true,
  documents: [
    {
      id: 31,
      filename: "risk-register.pdf",
      content_type: "application/pdf",
      file_size: 3971,
      status: "failed",
      created_at: "2026-07-30T10:00:00Z",
    },
  ],
  processing: {
    ...collectingStatus.processing,
    status: "failed",
    failed_jobs: 1,
    current_stage: "failed",
    current_stage_label: "Processing needs attention",
    total_documents: 1,
  },
};

const uploadedStatus = {
  ...collectingStatus,
  documents: [
    {
      id: 32,
      filename: "project-brief.pdf",
      content_type: "application/pdf",
      file_size: 3971,
      status: "uploaded",
      created_at: "2026-07-30T10:00:00Z",
    },
  ],
  processing: {
    ...collectingStatus.processing,
    total_documents: 1,
  },
};

const processingStatus = {
  ...uploadedStatus,
  status: "processing",
  uploads_locked: true,
  documents: [{ ...uploadedStatus.documents[0], status: "embedding" }],
  processing: {
    ...uploadedStatus.processing,
    status: "processing",
    queued_jobs: 1,
    current_stage: "embedding",
    current_stage_label: "Building the retrieval index",
  },
};

const readyStatus = {
  ...processingStatus,
  status: "ready",
  documents: [{ ...processingStatus.documents[0], status: "processed" }],
  processing: {
    ...processingStatus.processing,
    status: "ready",
    completed_jobs: 1,
    queued_jobs: 0,
    processed_documents: 1,
    current_stage: "ready",
    current_stage_label: "Evidence is ready for review",
  },
};

const evidenceSuggestions = [
  {
    question_key: "Q11",
    prompt: "Requirements are expected to materially change after delivery begins.",
    construct: "FLEXIBILITY",
    weight: 1,
    answer_type: "likert",
    proposed_value: "4",
    confidence: "high",
    evidence_status: "suggested",
    final_value: null,
    final_source: null,
    citations: [
      {
        document_id: 32,
        filename: "clinic-appointment-and-queue-portal-delivery-evidence.pdf",
        page_number: 2,
        excerpt: "Weekly clinician demonstrations are scheduled, and stories are refined with reception staff as delivery progresses.",
      },
    ],
  },
];

type DraftStatusFixture =
  | typeof collectingStatus
  | typeof failedStatus
  | typeof uploadedStatus
  | typeof processingStatus
  | typeof readyStatus;

const result = {
  submission_id: 47,
  recommendation: "Agile",
  agile_score: 78.4,
  traditional_score: 54.1,
  construct_scores: { FLEXIBILITY: 4, PERFORMANCE: 3, STRICTNESS: 2 },
  evidence_scoring: {
    questionnaire_construct_scores: { FLEXIBILITY: 4, PERFORMANCE: 3, STRICTNESS: 2 },
    document_construct_scores: { FLEXIBILITY: null, PERFORMANCE: null, STRICTNESS: null },
    document_coverage: { FLEXIBILITY: 0, PERFORMANCE: 0, STRICTNESS: 0 },
    document_contribution: { FLEXIBILITY: 0, PERFORMANCE: 0, STRICTNESS: 0 },
    decision_construct_scores: { FLEXIBILITY: 4, PERFORMANCE: 3, STRICTNESS: 2 },
    document_evidence_cap: 0.25,
    confirmed_item_count: 0,
  },
  dependent_variable_scores: { user_satisfaction: 4.1, timeline_adherence: 3.2 },
  comparison_series: {
    dimensions: ["Flexibility", "Performance", "Strictness"],
    project: [4, 3, 2],
    agile: [5, 3, 2],
    traditional: [2, 4, 5],
  },
  insights: {
    recommended_direction: "Agile",
    strongest_dimension: "Flexibility",
    strongest_score: 4,
    weakest_dimension: "Strictness",
    weakest_score: 2,
    score_gap: 24.3,
    confidence_level: "high",
  },
  decision_report: {
    recommendation: "Agile",
    confidence_level: "high",
    score_gap: 24.3,
    methodology_fit_summary: "Frequent change and accessible feedback favour iterative delivery.",
    outcome_scores: { user_satisfaction: 4.1, timeline_adherence: 3.2 },
    drivers: [
      { key: "flexibility", label: "Requirement change", methodology: "Agile", construct: "FLEXIBILITY", score: 4 },
    ],
    risk_flags: [],
    tradeoffs: {
      strengths: ["Short feedback cycles"],
      watch_areas: ["Protect governance checkpoints"],
      methodology_note: ["Keep the release plan visible."],
    },
    hypothesis_evidence: { H1: { label: "Flexibility", score: 4 } },
    strategy_profile: {
      hybrid_readiness: { score: 58, level: "moderate", rationale: ["Some governance controls remain useful."] },
      delivery_strategy: "iterative_delivery",
      strategy_options: [
        { key: "scrum", label: "Scrum", fit: "strong", reason: "Use short, reviewable delivery cycles." },
      ],
      governance_controls: ["Review scope and risk at each release boundary."],
      research_boundary_note: "Only Agile vs Traditional is empirically validated.",
    },
    next_steps: ["Confirm an empowered product owner.", "Define the first delivery increment."],
    limitations: ["Reassess if regulatory obligations change."],
  },
  ai_demo_trace: [],
  ai_demo_summary: {
    documents_processed: 0,
    trace_steps: 0,
    candidate_signals: [],
    document_filenames: [],
    demo_mode: true,
    explanation_scope: "questionnaire_only",
  },
  evidence_answers: [],
  traditional_advisor: { submission_id: 47, status: "not_applicable", retry_allowed: false, generated_at: null, error_message: null, advisor: null },
  rationale: "The project benefits from iterative planning and stakeholder feedback.",
  rules_version: 4,
  questionnaire_version: 3,
  created_at: "2026-07-30T10:00:00Z",
};

const envelope = (data: unknown, message = "OK") => ({
  status_code: 200,
  success: true,
  message,
  error_code: null,
  data,
});

async function fulfillJson(route: Route, data: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(data),
  });
}

async function mockAssessmentApi(
  page: Page,
  draftStatus: DraftStatusFixture | (() => DraftStatusFixture) = collectingStatus,
) {
  await page.route(/\/api\/v1\/questionnaire\/active$/, (route) => fulfillJson(route, envelope(questionnaire)));
  await page.route(/\/api\/v1\/assessments\/events$/, (route) =>
    fulfillJson(route, envelope({ session_id: "browser-session", status: "opened", answered_count: 0 })),
  );
  await page.route(/\/api\/v1\/assessment-drafts(?:\?.*)?$/, (route) =>
    fulfillJson(route, envelope({ draft_id: "browser-draft", status: "created" }), 201),
  );
  await page.route(/\/api\/v1\/assessment-drafts\/browser-draft\/documents\/status$/, (route) =>
    fulfillJson(route, envelope(typeof draftStatus === "function" ? draftStatus() : draftStatus)),
  );
}

test("participant completes a questionnaire and receives a recommendation", async ({ page }) => {
  await mockAssessmentApi(page);
  let submittedBody: Record<string, unknown> | null = null;
  await page.route(/\/api\/v1\/assessments$/, async (route) => {
    submittedBody = route.request().postDataJSON();
    await fulfillJson(route, envelope(result), 201);
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Begin assessment" }).click();
  await page.getByRole("textbox", { name: "Your response" }).fill("Maya Fernando");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue without documents" }).click();
  await page.getByRole("button", { name: "4" }).click();
  await expect(page.getByRole("heading", { name: "Check the project brief" })).toBeVisible();
  await page.getByRole("button", { name: "Calculate recommendation" }).click();

  await expect(page.getByRole("heading", { name: "Use Agile for Maya Fernando's project." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Head-to-head compatibility" })).toBeVisible();
  await expect(page.getByText("High confidence", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Analysis" }).click();
  await expect(page.getByRole("heading", { name: "What shaped this decision" })).toBeVisible();
  await page.getByRole("button", { name: "Explore project profile map" }).click();
  await expect(page.getByRole("heading", { name: "Dimension Comparison" })).toBeVisible();
  expect(submittedBody).toMatchObject({
    profile: { name: "Maya Fernando" },
    answers: [{ question_key: "Q11", construct: "FLEXIBILITY", value: 4 }],
    draft_id: "browser-draft",
  });
});

test("terminal document failure is shown as failed instead of processing forever", async ({ page }) => {
  await mockAssessmentApi(page, failedStatus);
  await page.goto("/");
  await page.getByRole("button", { name: "Begin assessment" }).click();
  await page.getByRole("textbox", { name: "Your response" }).fill("Maya Fernando");
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByText(/could not be processed/i)).toBeVisible();
  await expect(page.getByText("Needs attention", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Continue without documents" })).toBeEnabled();
  await expect(page.getByText("Processing evidence")).toHaveCount(0);
});

test("participant answers Likert questions while document evidence is processing", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 900 });
  let currentStatus: DraftStatusFixture = collectingStatus;
  await mockAssessmentApi(page, () => currentStatus);
  await page.route(/\/api\/v1\/assessment-drafts\/browser-draft\/consent$/, (route) => fulfillJson(route, envelope(collectingStatus)));
  await page.route(/\/api\/v1\/assessment-drafts\/browser-draft\/documents$/, (route) => {
    currentStatus = uploadedStatus;
    return fulfillJson(route, envelope(uploadedStatus.documents[0]), 201);
  });
  await page.route(/\/api\/v1\/assessment-drafts\/browser-draft\/process$/, (route) => {
    currentStatus = processingStatus;
    return fulfillJson(route, envelope(processingStatus), 202);
  });
  await page.route(/\/api\/v1\/assessment-drafts\/browser-draft\/evidence-answers$/, (route) => fulfillJson(route, envelope(evidenceSuggestions)));

  await page.goto("/");
  await page.getByRole("button", { name: "Begin assessment" }).click();
  await page.getByRole("textbox", { name: "Your response" }).fill("Maya Fernando");
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByRole("checkbox").nth(0).check();
  await page.getByRole("checkbox").nth(1).check();
  await page.getByRole("button", { name: "Select PDF" }).click();
  await page.locator('input[type="file"]').setInputFiles({
    name: "project-brief.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4 project brief"),
  });
  await expect(page.getByRole("button", { name: "Analyze 1 document" })).toBeVisible();
  await page.getByRole("button", { name: "Analyze 1 document" }).click();

  await expect(page.getByRole("heading", { name: "How much are requirements expected to change?" })).toBeVisible();
  await expect(page.getByText("Reading your document")).toBeVisible();
  await expect(page.getByText("Finding relevant project details")).toBeVisible();
  await expect(page.getByText("Preparing suggestions for review")).toBeVisible();

  currentStatus = readyStatus;
  await page.getByRole("button", { name: "4" }).click();
  const reviewHeading = page.getByRole("heading", { name: "Confirm document-backed signals" });
  await expect(reviewHeading).toBeVisible({ timeout: 5_000 });

  const reviewPanel = reviewHeading.locator("xpath=ancestor::section[1]");
  const panelBox = await reviewPanel.boundingBox();
  const confidenceBox = await page.getByText("high confidence", { exact: true }).boundingBox();
  const scoreBox = await page.getByText("Extracted score", { exact: true }).boundingBox();

  expect(panelBox?.width).toBeGreaterThan(1_200);
  expect(1_600 - ((panelBox?.x ?? 0) + (panelBox?.width ?? 0))).toBeGreaterThanOrEqual(40);
  expect(1_600 - ((panelBox?.x ?? 0) + (panelBox?.width ?? 0))).toBeLessThanOrEqual(56);
  expect(confidenceBox?.x).toBeGreaterThan((panelBox?.x ?? 0) + (panelBox?.width ?? 0) - 230);
  expect(scoreBox?.x).toBeGreaterThan((panelBox?.x ?? 0) + (panelBox?.width ?? 0) - 230);
});

test("@mobile landing and assessment shell do not overflow horizontally", async ({ page }) => {
  await mockAssessmentApi(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Find the delivery method/ })).toBeVisible();
  const landingOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(landingOverflow).toBeLessThanOrEqual(1);

  await page.getByRole("button", { name: "Begin assessment" }).click();
  await expect(page.getByRole("textbox", { name: "Your response" })).toBeVisible();
  const formOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(formOverflow).toBeLessThanOrEqual(1);
});
