import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DocumentUploadScreen from "@/components/DocumentUploadScreen";
import {
  getDraftStatus,
  recordDraftConsent,
  startDocumentProcessing,
  uploadDocument,
  type DraftStatusResponse,
} from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    deleteDraftDocument: vi.fn(),
    getDraftStatus: vi.fn(),
    recordDraftConsent: vi.fn(),
    startDocumentProcessing: vi.fn(),
    uploadDocument: vi.fn(),
  };
});

const status = (overrides: Partial<DraftStatusResponse> = {}): DraftStatusResponse => ({
  draft_id: "draft-test",
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
  ...overrides,
});

describe("DocumentUploadScreen", () => {
  beforeEach(() => vi.clearAllMocks());

  it("requires both consent statements before opening file selection", async () => {
    vi.mocked(getDraftStatus).mockResolvedValue(status());
    const user = userEvent.setup();
    render(<DocumentUploadScreen draftId="draft-test" onContinue={vi.fn()} onProcessingStarted={vi.fn()} onSkip={vi.fn()} />);
    await screen.findByText("Attach a project PDF");
    await user.click(screen.getByRole("button", { name: "Select PDF" }));
    expect(screen.getByText("Confirm both document-processing statements before selecting a PDF.")).toBeVisible();
    expect(recordDraftConsent).not.toHaveBeenCalled();
  });

  it("records consent, validates PDF input, and uploads a valid file", async () => {
    const uploadedStatus = status({
      documents: [{
        id: 8,
        filename: "delivery-brief.pdf",
        content_type: "application/pdf",
        file_size: 128,
        status: "uploaded",
        created_at: "2026-07-30T10:00:00Z",
      }],
    });
    vi.mocked(getDraftStatus).mockResolvedValueOnce(status()).mockResolvedValue(uploadedStatus);
    vi.mocked(recordDraftConsent).mockResolvedValue(status());
    vi.mocked(uploadDocument).mockResolvedValue(uploadedStatus.documents[0]);
    const user = userEvent.setup();
    const { container } = render(
      <DocumentUploadScreen draftId="draft-test" onContinue={vi.fn()} onProcessingStarted={vi.fn()} onSkip={vi.fn()} />,
    );
    await screen.findByText("Attach a project PDF");
    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[0]);
    await user.click(checkboxes[1]);
    await user.click(screen.getByRole("button", { name: "Select PDF" }));
    expect(recordDraftConsent).toHaveBeenCalledWith("draft-test");

    const input = container.querySelector<HTMLInputElement>('input[type="file"]');
    expect(input).not.toBeNull();
    const pdf = new File(["selectable project brief"], "delivery-brief.pdf", { type: "application/pdf" });
    await user.upload(input as HTMLInputElement, pdf);
    await waitFor(() => expect(uploadDocument).toHaveBeenCalledWith("draft-test", pdf));
    expect(await screen.findByText("delivery-brief.pdf")).toBeVisible();
  });

  it("starts one explicit batch after documents are collected", async () => {
    const collected = status({
      documents: [{
        id: 3,
        filename: "project-governance.pdf",
        content_type: "application/pdf",
        file_size: 512,
        status: "uploaded",
        created_at: "2026-07-30T10:00:00Z",
      }],
      processing: { ...status().processing, total_documents: 1 },
    });
    const processing = status({
      status: "processing",
      uploads_locked: true,
      documents: [{ ...collected.documents[0], status: "embedding" }],
      processing: {
        ...collected.processing,
        status: "processing",
        queued_jobs: 1,
        current_stage: "embedding",
        current_stage_label: "Building the retrieval index",
      },
    });
    vi.mocked(getDraftStatus).mockResolvedValue(collected);
    vi.mocked(startDocumentProcessing).mockResolvedValue(processing);
    const user = userEvent.setup();
    const onProcessingStarted = vi.fn();
    render(<DocumentUploadScreen draftId="draft-test" onContinue={vi.fn()} onProcessingStarted={onProcessingStarted} onSkip={vi.fn()} />);
    await user.click(await screen.findByRole("button", { name: "Analyze 1 document" }));
    expect(startDocumentProcessing).toHaveBeenCalledWith("draft-test");
    expect(onProcessingStarted).toHaveBeenCalledWith(processing);
    expect(await screen.findByText("Finding relevant project details")).toBeVisible();
    expect(screen.getByText("Reading your document")).toBeVisible();
    expect(screen.getByText("Preparing suggestions for review")).toBeVisible();
  });

  it("stops the processing state and offers a manual path after terminal failure", async () => {
    const failed = status({
      status: "failed",
      uploads_locked: true,
      documents: [{
        id: 11,
        filename: "risk-register.pdf",
        content_type: "application/pdf",
        file_size: 1024,
        status: "failed",
        created_at: "2026-07-30T10:00:00Z",
      }],
      processing: {
        ...status().processing,
        status: "failed",
        failed_jobs: 1,
        current_stage: "failed",
        current_stage_label: "Processing needs attention",
        total_documents: 1,
      },
    });
    vi.mocked(getDraftStatus).mockResolvedValue(failed);
    const onSkip = vi.fn();
    const user = userEvent.setup();
    render(<DocumentUploadScreen draftId="draft-test" onContinue={vi.fn()} onProcessingStarted={vi.fn()} onSkip={onSkip} />);

    expect(await screen.findByText(/could not be processed/i)).toBeVisible();
    expect(screen.getByText("Needs attention")).toBeVisible();
    expect(screen.queryByText("Processing evidence")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue without documents" }));
    expect(onSkip).toHaveBeenCalledOnce();
  });

  it("continues to methodology questions when processing is ready", async () => {
    const ready = status({
      status: "ready",
      uploads_locked: true,
      documents: [{
        id: 4,
        filename: "scope.pdf",
        content_type: "application/pdf",
        file_size: 640,
        status: "processed",
        created_at: "2026-07-30T10:00:00Z",
      }],
      processing: {
        ...status().processing,
        status: "ready",
        completed_jobs: 1,
        processed_documents: 1,
        total_documents: 1,
      },
    });
    vi.mocked(getDraftStatus).mockResolvedValue(ready);
    const onContinue = vi.fn();
    const user = userEvent.setup();
    render(<DocumentUploadScreen draftId="draft-test" onContinue={onContinue} onProcessingStarted={vi.fn()} onSkip={vi.fn()} />);
    await user.click(await screen.findByRole("button", { name: "Continue to methodology questions" }));
    expect(onContinue).toHaveBeenCalledOnce();
  });
});
