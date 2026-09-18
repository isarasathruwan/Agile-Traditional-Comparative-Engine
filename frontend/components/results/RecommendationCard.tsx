interface RecommendationCardProps {
  recommendation: string;
  reason: string;
  name: string;
  score: number;
  confidenceLevel: "high" | "moderate" | "close";
  scoreGap: number;
}

export default function RecommendationCard({
  recommendation,
  reason,
  name,
  score,
  confidenceLevel,
  scoreGap,
}: RecommendationCardProps) {
  const confidenceLabel =
    confidenceLevel === "high"
      ? "High confidence"
      : confidenceLevel === "moderate"
        ? "Moderate confidence"
        : "Close decision";
  const confidenceTone =
    confidenceLevel === "high"
      ? "border-blue-700 bg-blue-50 text-blue-800"
      : confidenceLevel === "moderate"
        ? "border-amber-700 bg-amber-50 text-amber-800"
        : "border-slate-700 bg-slate-100 text-slate-800";

  return (
    <section className="border-y border-slate-300 bg-white px-5 py-8 sm:px-7">
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_220px] lg:items-end">
        <div>
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Methodology decision brief
          </p>
          <h2 className="mt-4 max-w-4xl text-3xl font-semibold leading-tight tracking-tight text-slate-950 sm:text-4xl">
            Use {recommendation} as the primary delivery direction{name ? ` for ${name}` : ""}.
          </h2>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600">{reason}</p>
          <div className="mt-6 flex flex-wrap gap-2 text-xs font-semibold">
            <span className={["border px-3 py-1", confidenceTone].join(" ")}>
              {confidenceLabel}
            </span>
            <span className="border border-slate-300 bg-white px-3 py-1 text-slate-700">
              {scoreGap.toFixed(1)} point method gap
            </span>
          </div>
        </div>

        <div className="border-l border-slate-300 pl-5">
          <p className="font-mono text-xs font-semibold uppercase tracking-wide text-slate-500">Fit score</p>
          <p className="mt-3 font-mono text-5xl font-semibold tracking-tight text-slate-950">
            {score}
            <span className="text-2xl text-slate-400">/100</span>
          </p>
          <div className="mt-4 h-1.5 bg-slate-200">
            <div className="h-1.5 bg-blue-700" style={{ width: `${Math.min(100, Math.max(0, score))}%` }} />
          </div>
        </div>
      </div>
    </section>
  );
}
