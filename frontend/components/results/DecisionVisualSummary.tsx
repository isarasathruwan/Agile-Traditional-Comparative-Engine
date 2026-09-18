import { confidenceBand } from "@/lib/resultAnalytics";

type Props = {
  agileScore: number;
  traditionalScore: number;
  recommendation: "Agile" | "Traditional";
  scoreGap: number;
};

function boundedScore(score: number) {
  return Math.min(100, Math.max(0, score));
}

export default function DecisionVisualSummary({ agileScore, traditionalScore, recommendation, scoreGap }: Props) {
  const confidence = confidenceBand(scoreGap);
  const leadingScore = recommendation === "Agile" ? agileScore : traditionalScore;
  const trailingScore = recommendation === "Agile" ? traditionalScore : agileScore;
  const rulerPosition = Math.min(scoreGap, 20) / 20 * 100;

  return (
    <section aria-labelledby="decision-visual-summary-title" className="grid gap-6 border-y border-slate-200 py-5 lg:grid-cols-[minmax(0,1fr)_230px] lg:gap-8">
      <div>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-blue-700">Methodology fit</p>
            <h2 id="decision-visual-summary-title" className="mt-1 text-lg font-semibold tracking-tight text-slate-950">Head-to-head compatibility</h2>
          </div>
          <p className="font-mono text-sm font-semibold text-slate-700">{scoreGap.toFixed(1)} point margin</p>
        </div>

        <div className="mt-5 space-y-4">
          <ScoreRow label="Agile" score={agileScore} isRecommended={recommendation === "Agile"} />
          <ScoreRow label="Traditional" score={traditionalScore} isRecommended={recommendation === "Traditional"} />
        </div>
        <p className="mt-4 text-xs leading-5 text-slate-500">
          {recommendation} leads by {Math.abs(leadingScore - trailingScore).toFixed(1)} points against the active reference profiles.
        </p>
      </div>

      <div className="border-t border-slate-200 pt-5 lg:border-l lg:border-t-0 lg:pl-7 lg:pt-0">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Decision confidence</p>
        <p className="mt-2 text-xl font-semibold tracking-tight text-slate-950">{confidence.label}</p>
        <p className="mt-1 text-sm leading-5 text-slate-600">{confidence.description}</p>
        <div className="mt-5" role="img" aria-label={`${confidence.label}: ${scoreGap.toFixed(1)} point score gap. Close below 10, moderate from 10 to 19.9, high from 20 points.`}>
          <div className="relative h-2 bg-slate-200">
            <span className="absolute inset-y-0 left-1/2 border-l border-slate-400" aria-hidden="true" />
            <span className="absolute inset-y-0 right-0 border-l border-slate-600" aria-hidden="true" />
            <span className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-blue-700 shadow-sm" style={{ left: `${rulerPosition}%` }} aria-hidden="true" />
          </div>
          <div className="mt-2 grid grid-cols-3 text-[10px] font-medium uppercase tracking-[0.1em] text-slate-500">
            <span>Close</span><span className="text-center">Moderate</span><span className="text-right">High</span>
          </div>
          <div className="mt-1 grid grid-cols-3 font-mono text-[10px] text-slate-400"><span>0</span><span className="text-center">10</span><span className="text-right">20+</span></div>
        </div>
      </div>
    </section>
  );
}

function ScoreRow({ label, score, isRecommended }: { label: string; score: number; isRecommended: boolean }) {
  const fillClass = isRecommended ? "bg-blue-700" : "bg-slate-500";

  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-sm">
        <p className="font-semibold text-slate-900">{label}{isRecommended ? <span className="ml-2 text-xs font-semibold text-blue-700">Recommended</span> : null}</p>
        <p className="font-mono font-semibold text-slate-700">{score.toFixed(1)}<span className="text-slate-400">/100</span></p>
      </div>
      <div className="mt-2 h-2 overflow-hidden bg-slate-200" role="img" aria-label={`${label} compatibility score ${score.toFixed(1)} out of 100`}>
        <div className={`h-full transition-[width] duration-300 ease-out motion-reduce:transition-none ${fillClass}`} style={{ width: `${boundedScore(score)}%` }} />
      </div>
    </div>
  );
}
