import { ArrowRight, PencilSimple } from "@phosphor-icons/react";
import type { LikertQuestion, ProfileQuestion } from "@/lib/api";

interface AssessmentReviewProps {
  profileQuestions: ProfileQuestion[];
  likertQuestions: LikertQuestion[];
  profile: Record<string, string>;
  profileOtherInputs: Record<string, string>;
  answers: Record<string, number>;
  onEditProfile: (index: number) => void;
  onEditLikert: (index: number) => void;
  onContinue: () => void;
  isPreparing: boolean;
}

export default function AssessmentReview({
  profileQuestions,
  likertQuestions,
  profile,
  profileOtherInputs,
  answers,
  onEditProfile,
  onEditLikert,
  onContinue,
  isPreparing,
}: AssessmentReviewProps) {
  const profileAnswer = (question: ProfileQuestion) => {
    const value = profile[question.profile_key] ?? "";
    return value.toLowerCase() === "other" && profileOtherInputs[question.profile_key]
      ? `Other: ${profileOtherInputs[question.profile_key]}`
      : value;
  };

  return (
    <section className="border-y border-slate-200 bg-white px-5 py-8 sm:border sm:px-10 sm:py-11">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">Review</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-[2.15rem]">Check the project brief</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
        Confirm the answers below before calculating the recommendation. You can revise an individual answer without repeating the assessment.
      </p>

      <div className="mt-9 divide-y divide-slate-200 border-y border-slate-200">
        <ReviewGroup title="Project context">
          {profileQuestions.map((question, index) => (
            <ReviewRow
              key={question.question_id}
              label={question.prompt}
              value={profileAnswer(question)}
              onEdit={() => onEditProfile(index)}
            />
          ))}
        </ReviewGroup>
        <ReviewGroup title="Method fit signals">
          {likertQuestions.map((question, index) => {
            const value = answers[question.question_id];
            return (
              <ReviewRow
                key={question.question_id}
                label={question.prompt}
                value={value === undefined ? "Not answered" : `${value}/5 · ${question.scale_labels[value - 1]}`}
                onEdit={() => onEditLikert(index)}
              />
            );
          })}
        </ReviewGroup>
      </div>

      <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-slate-500">Document-backed values remain traceable in the final result.</p>
        <button
          type="button"
          onClick={onContinue}
          disabled={isPreparing}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-blue-700 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-800 active:translate-y-px disabled:cursor-wait disabled:bg-slate-400"
        >
          {isPreparing ? "Calculating..." : "Calculate recommendation"}
          <ArrowRight size={16} weight="bold" />
        </button>
      </div>
    </section>
  );
}

function ReviewGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="py-6 first:pt-6 last:pb-6">
      <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{title}</h2>
      <div className="mt-3 divide-y divide-slate-100">{children}</div>
    </section>
  );
}

function ReviewRow({ label, value, onEdit }: { label: string; value: string; onEdit: () => void }) {
  return (
    <div className="grid gap-2 py-3 sm:grid-cols-[minmax(0,1fr)_minmax(150px,0.7fr)_auto] sm:items-center sm:gap-5">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="truncate text-sm font-semibold text-slate-900" title={value}>{value || "Not provided"}</p>
      <button type="button" onClick={onEdit} className="inline-flex w-fit items-center gap-1.5 text-sm font-semibold text-blue-700 hover:text-blue-900">
        <PencilSimple size={15} weight="bold" />
        Edit
      </button>
    </div>
  );
}
