import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import DecisionVisualSummary from "@/components/results/DecisionVisualSummary";
import EvidenceContributionPanel from "@/components/results/EvidenceContributionPanel";

describe("result visuals", () => {
  it("communicates the winning method and high-confidence threshold", () => {
    render(<DecisionVisualSummary agileScore={78.4} traditionalScore={54.1} recommendation="Agile" scoreGap={24.3} />);

    expect(screen.getByRole("heading", { name: "Head-to-head compatibility" })).toBeVisible();
    expect(screen.getByText("High confidence", { exact: true })).toBeVisible();
    expect(screen.getByText("24.3 point margin", { exact: true })).toBeVisible();
    expect(screen.getByRole("img", { name: /high confidence: 24.3 point score gap/i })).toBeVisible();
  });

  it("shows construct coverage and opens the evidence tab on request", async () => {
    const user = userEvent.setup();
    const onReviewEvidence = vi.fn();
    render(
      <EvidenceContributionPanel
        confirmedItemCount={2}
        documentEvidenceCap={0.25}
        documentCoverage={{ FLEXIBILITY: 1, PERFORMANCE: 0.5, STRICTNESS: 0 }}
        documentContribution={{ FLEXIBILITY: 0.25, PERFORMANCE: 0.125, STRICTNESS: 0 }}
        onReviewEvidence={onReviewEvidence}
      />,
    );

    expect(screen.getByText(/2 cited document-only signals were confirmed/i)).toBeVisible();
    expect(screen.getByText("Average coverage").parentElement).toHaveTextContent("50%");
    await user.click(screen.getByRole("button", { name: "Review cited evidence" }));
    expect(onReviewEvidence).toHaveBeenCalledOnce();
  });
});
