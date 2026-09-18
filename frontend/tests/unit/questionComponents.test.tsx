import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AssessmentReview from "@/components/AssessmentReview";
import LikertScreen from "@/components/LikertScreen";
import PillSelectQuestion from "@/components/PillSelectQuestion";
import TextQuestion from "@/components/TextQuestion";

describe("question components", () => {
  it("validates and submits a text response", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    const { rerender } = render(
      <TextQuestion question="Project name" placeholder="Name" value="" onChange={onChange} onSubmit={onSubmit} />,
    );

    const input = screen.getByRole("textbox", { name: "Your response" });
    await user.type(input, "A");
    expect(onChange).toHaveBeenCalledWith("A");
    rerender(
      <TextQuestion question="Project name" placeholder="Name" value="A" onChange={onChange} onSubmit={onSubmit} />,
    );
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByText("Please enter at least 2 characters.")).toBeVisible();
    expect(onSubmit).not.toHaveBeenCalled();

    rerender(
      <TextQuestion question="Project name" placeholder="Name" value="Operations Renewal" onChange={onChange} onSubmit={onSubmit} />,
    );
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("requires a meaningful custom value for Other", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <PillSelectQuestion question="Project type" options={["Migration", "Other"]} onSelect={onSelect} />,
    );

    await user.click(screen.getByRole("button", { name: "Other" }));
    const custom = screen.getByRole("textbox", { name: "Please specify" });
    await user.type(custom, "x");
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByText("Please enter at least 2 characters.")).toBeVisible();
    expect(onSelect).not.toHaveBeenCalled();

    await user.clear(custom);
    await user.type(custom, "Platform Modernization");
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(onSelect).toHaveBeenCalledWith("Other", "Platform Modernization");
  });

  it("locks a Likert choice after recording one answer", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <LikertScreen
        construct="Delivery constraints"
        question="How fixed is the deadline?"
        scaleLabels={["Flexible", "Mostly flexible", "Moderate", "Fixed", "Immovable"]}
        onSelect={onSelect}
      />,
    );
    await user.click(screen.getByRole("button", { name: "4" }));
    expect(onSelect).toHaveBeenCalledWith(4);
    expect(screen.getByRole("button", { name: "1" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "4" })).toBeDisabled();
  });

  it("renders review answers and routes edit actions", async () => {
    const user = userEvent.setup();
    const onEditProfile = vi.fn();
    const onEditLikert = vi.fn();
    const onContinue = vi.fn();
    render(
      <AssessmentReview
        profileQuestions={[
          { question_id: "Q1", kind: "text", profile_key: "name", prompt: "Name" },
          { question_id: "Q2", kind: "pill", profile_key: "role", prompt: "Role", options: ["Other"] },
        ]}
        likertQuestions={[
          {
            question_id: "Q11",
            construct: "FLEXIBILITY",
            prompt: "Requirement change",
            scale_labels: ["Stable", "Low", "Medium", "High", "Constant"],
          },
        ]}
        profile={{ name: "Maya Fernando", role: "Other" }}
        profileOtherInputs={{ role: "Delivery Lead" }}
        answers={{ Q11: 4 }}
        isPreparing={false}
        onEditProfile={onEditProfile}
        onEditLikert={onEditLikert}
        onContinue={onContinue}
      />,
    );

    expect(screen.getByText("Maya Fernando")).toBeVisible();
    expect(screen.getByText("Other: Delivery Lead")).toBeVisible();
    expect(screen.getByText("4/5 · High")).toBeVisible();
    const editButtons = screen.getAllByRole("button", { name: "Edit" });
    await user.click(editButtons[0]);
    await user.click(editButtons[2]);
    await user.click(screen.getByRole("button", { name: "Calculate recommendation" }));
    expect(onEditProfile).toHaveBeenCalledWith(0);
    expect(onEditLikert).toHaveBeenCalledWith(0);
    expect(onContinue).toHaveBeenCalledOnce();
  });
});
