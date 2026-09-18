"use client";

import { CheckCircle, SpinnerGap } from "@phosphor-icons/react";

interface DocumentProcessingStepsProps {
  currentStage: string;
  compact?: boolean;
}

const PROCESSING_STEPS = [
  "Reading your document",
  "Finding relevant project details",
  "Preparing suggestions for review",
] as const;

function currentStepIndex(currentStage: string) {
  if (currentStage === "ready") return PROCESSING_STEPS.length;
  if (currentStage === "reasoning") return 2;
  if (currentStage === "embedding") return 1;
  return 0;
}

export default function DocumentProcessingSteps({ currentStage, compact = false }: DocumentProcessingStepsProps) {
  const activeStep = currentStepIndex(currentStage);

  return (
    <ol className={compact ? "mt-3 space-y-2" : "mt-7 divide-y divide-slate-200 border-y border-slate-200"}>
      {PROCESSING_STEPS.map((label, index) => {
        const isComplete = index < activeStep;
        const isCurrent = index === activeStep;
        return (
          <li key={label} className={`flex items-center gap-3 ${compact ? "" : "py-3"}`}>
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                isComplete
                  ? "border-blue-700 bg-blue-700 text-white"
                  : isCurrent
                    ? "border-blue-700 bg-white text-blue-700"
                    : "border-slate-300 bg-white text-slate-400"
              }`}
            >
              {isComplete ? (
                <CheckCircle size={12} weight="bold" />
              ) : isCurrent ? (
                <SpinnerGap size={12} className="animate-spin" weight="bold" />
              ) : (
                <span className="text-[10px] font-semibold">{index + 1}</span>
              )}
            </span>
            <p className={`text-sm font-medium ${isComplete || isCurrent ? "text-slate-900" : "text-slate-500"}`}>{label}</p>
          </li>
        );
      })}
    </ol>
  );
}
