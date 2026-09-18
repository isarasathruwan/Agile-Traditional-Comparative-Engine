import { CheckCircle, FlagBanner, ShieldCheck, Strategy, Warning } from "@phosphor-icons/react";
import type { AssessmentCreateResponse } from "@/lib/api";
import GuidanceCallout from "@/components/results/GuidanceCallout";

type Props = {
  result: AssessmentCreateResponse;
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

export default function DecisionReport({ result }: Props) {
  const report = result.decision_report;
  const strategy = report.strategy_profile;
  const selectedScore = report.recommendation === "Agile" ? result.agile_score : result.traditional_score;
  const alternateScore = report.recommendation === "Agile" ? result.traditional_score : result.agile_score;
  const alternateMethod = report.recommendation === "Agile" ? "Traditional" : "Agile";
  const confidenceLabel =
    report.confidence_level === "high"
      ? "High confidence"
      : report.confidence_level === "moderate"
        ? "Moderate confidence"
        : "Close decision";
  const readinessTone =
    strategy.hybrid_readiness.level === "high"
      ? "bg-blue-700"
      : strategy.hybrid_readiness.level === "moderate"
        ? "bg-amber-600"
        : "bg-slate-500";
  const watchArea = report.risk_flags[0]?.label ?? report.tradeoffs.watch_areas[0];
  const decisionFlags = [
    {
      key: "confidence",
      icon: report.confidence_level === "close" ? Warning : CheckCircle,
      label: confidenceLabel,
      body:
        report.confidence_level === "close"
          ? "The score gap is narrow. Review the evidence before committing."
          : `${report.score_gap.toFixed(1)} point gap between methods.`,
    },
    watchArea
      ? {
          key: "watch",
          icon: FlagBanner,
          label: "Watch area",
          body: watchArea,
        }
      : null,
    report.next_steps[0]
      ? {
          key: "next",
          icon: Strategy,
          label: "Next action",
          body: report.next_steps[0],
        }
      : null,
  ].filter(Boolean) as Array<{
    key: string;
    icon: typeof Warning;
    label: string;
    body: string;
  }>;

  return (
    <section className="space-y-10">
      <section className="grid gap-8 border-b border-slate-300 pb-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div>
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Recommendation logic
          </p>
          <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
            The engine places this project closer to {report.recommendation}.
          </h3>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{report.methodology_fit_summary}</p>
          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <MethodScore label={report.recommendation} score={selectedScore} active />
            <MethodScore label={alternateMethod} score={alternateScore} />
          </div>
        </div>

        <div className="border-l border-slate-300 pl-5">
          <p className="font-mono text-xs font-semibold uppercase tracking-wide text-slate-500">Decision-signal profile</p>
          <div className="mt-4 space-y-4">
            {Object.entries(report.outcome_scores).map(([key, value]) => (
              <MeterRow key={key} label={formatLabel(key)} value={value} max={5} valueLabel={`${value.toFixed(2)} / 5`} />
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-slate-300 pb-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Decision flags</p>
            <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">What needs attention</h3>
          </div>
          <span className="border border-slate-300 bg-white px-3 py-1 font-mono text-xs font-semibold uppercase tracking-wide text-slate-600">
            {report.risk_flags.length} risk signals
          </span>
        </div>
        <div className="mt-5 divide-y divide-slate-200 border-y border-slate-200">
          {decisionFlags.map((flag) => {
            const Icon = flag.icon;
            return (
              <div key={flag.key} className="grid gap-3 py-4 sm:grid-cols-[180px_minmax(0,1fr)]">
                <p className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Icon size={18} weight="bold" className="text-blue-700" aria-hidden="true" />
                  {flag.label}
                </p>
                <p className="text-sm leading-6 text-slate-600">{flag.body}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="grid gap-8 border-b border-slate-300 pb-8 lg:grid-cols-[1fr_0.9fr]">
        <div>
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Action plan</p>
          <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">What to do next</h3>
          <ol className="mt-5 divide-y divide-slate-200 border-y border-slate-200">
            {report.next_steps.map((step, index) => (
              <li key={step} className="grid gap-3 py-4 sm:grid-cols-[48px_minmax(0,1fr)]">
                <span className="font-mono text-sm font-semibold text-slate-500">{String(index + 1).padStart(2, "0")}</span>
                <span className="text-sm leading-6 text-slate-700">{step}</span>
              </li>
            ))}
          </ol>
        </div>

        <div>
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Governance controls</p>
          <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">Keep delivery controlled</h3>
          <div className="mt-5 divide-y divide-slate-200 border-y border-slate-200">
            {strategy.governance_controls.map((control) => (
              <p key={control} className="flex gap-3 py-4 text-sm leading-6 text-slate-700">
                <ShieldCheck size={18} weight="bold" className="mt-1 shrink-0 text-blue-700" aria-hidden="true" />
                {control}
              </p>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-8 border-b border-slate-300 pb-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div>
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Advisory strategy</p>
          <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
            {formatLabel(strategy.delivery_strategy)}
          </h3>
          <div className="mt-5 divide-y divide-slate-200 border-y border-slate-200">
            {strategy.strategy_options.map((option) => (
              <div key={option.key} className="grid gap-3 py-4 sm:grid-cols-[180px_minmax(0,1fr)]">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{option.label}</p>
                  <p className="mt-1 font-mono text-xs uppercase tracking-wide text-blue-700">{option.fit}</p>
                </div>
                <p className="text-sm leading-6 text-slate-600">{option.reason}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="border-l border-slate-300 pl-5">
          <p className="font-mono text-xs font-semibold uppercase tracking-wide text-slate-500">
            Hybrid readiness
          </p>
          <div className="mt-3 flex items-end justify-between gap-3">
            <p className="capitalize text-2xl font-semibold tracking-tight text-slate-950">
              {strategy.hybrid_readiness.level}
            </p>
            <p className="font-mono text-sm font-semibold text-slate-600">{strategy.hybrid_readiness.score}/100</p>
          </div>
          <div className="mt-3 h-1.5 bg-slate-200">
            <div
              className={["h-1.5", readinessTone].join(" ")}
              style={{ width: `${Math.min(100, strategy.hybrid_readiness.score)}%` }}
            />
          </div>
          <div className="mt-5 space-y-3">
            {strategy.hybrid_readiness.rationale.map((item) => (
              <p key={item} className="text-xs leading-5 text-slate-600">
                {item}
              </p>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div>
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Evidence summary</p>
          <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">Why the engine leaned this way</h3>
          <div className="mt-5 grid gap-6 md:grid-cols-2">
            <EvidenceList title="Strengths" items={report.tradeoffs.strengths} />
            <EvidenceList title="Watch areas" items={report.tradeoffs.watch_areas} />
          </div>
          <div className="mt-6">
            <EvidenceList title="Methodology notes" items={report.tradeoffs.methodology_note} />
          </div>
        </div>

        <div className="space-y-4">
          <GuidanceCallout tone="info" title="Decision-support note">
            {report.limitations.join(" ")}
          </GuidanceCallout>
        </div>
      </section>

      <details className="border-y border-slate-300 py-4">
        <summary className="cursor-pointer text-sm font-semibold text-slate-900">Assessment inputs</summary>
        <div className="mt-4 divide-y divide-slate-200 border-t border-slate-200">
          {Object.entries(report.hypothesis_evidence).map(([key, evidence]) => (
            <p key={key} className="grid gap-2 py-3 text-sm leading-6 text-slate-600 sm:grid-cols-[90px_minmax(0,1fr)]">
              <span className="font-mono text-xs font-semibold uppercase text-slate-500">{key}</span>
              <span>
                {evidence.label} ({evidence.score.toFixed(2)})
              </span>
            </p>
          ))}
        </div>
      </details>
    </section>
  );
}

function MethodScore({ label, score, active = false }: { label: string; score: number; active?: boolean }) {
  return (
    <div className="border-t border-slate-300 pt-4">
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm font-semibold text-slate-900">{label}</p>
        <p className="font-mono text-sm font-semibold text-slate-600">{Math.round(score)}/100</p>
      </div>
      <div className="mt-3 h-1.5 bg-slate-200">
        <div
          className={["h-1.5", active ? "bg-blue-700" : "bg-slate-500"].join(" ")}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  );
}

function MeterRow({
  label,
  value,
  max,
  valueLabel,
}: {
  label: string;
  value: number;
  max: number;
  valueLabel: string;
}) {
  return (
    <div>
      <div className="flex justify-between gap-3 text-xs text-slate-500">
        <span>{label}</span>
        <span className="font-mono">{valueLabel}</span>
      </div>
      <div className="mt-1.5 h-1.5 bg-slate-200">
        <div className="h-1.5 bg-slate-700" style={{ width: `${Math.min(100, (value / max) * 100)}%` }} />
      </div>
    </div>
  );
}

function EvidenceList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) {
    return null;
  }

  return (
    <div>
      <p className="text-sm font-semibold text-slate-900">{title}</p>
      <div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">
        {items.map((item) => (
          <p key={item} className="py-3 text-sm leading-6 text-slate-600">
            {item}
          </p>
        ))}
      </div>
    </div>
  );
}
