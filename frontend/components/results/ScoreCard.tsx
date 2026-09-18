interface ScoreCardProps {
  label: string;
  score: number;
  tone: "blue" | "slate";
}

export default function ScoreCard({
  label,
  score,
  tone,
}: ScoreCardProps) {
  const barToneClass = tone === "blue" ? "bg-blue-700" : "bg-slate-500";
  const scoreToneClass = tone === "blue" ? "text-blue-800" : "text-slate-700";
  const labelToneClass = tone === "blue" ? "text-blue-800" : "text-slate-600";

  return (
    <section className="border-t border-slate-300 bg-white py-5">
      <p className={["font-mono text-xs font-semibold uppercase tracking-wide", labelToneClass].join(" ")}>
        {label}
      </p>
      <div className="mt-5 h-1.5 w-full bg-slate-200">
        <div
          className={["h-1.5", barToneClass].join(" ")}
          style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
          role="img"
          aria-label={`${label} score ${score} out of 100`}
        />
      </div>
      <div className="mt-5">
        <p className={["font-mono text-4xl font-semibold", scoreToneClass].join(" ")}>
          {score}
          <span className="ml-1 text-2xl text-slate-400">/100</span>
        </p>
        <p className="mt-1 text-sm text-slate-500">Composite compatibility score</p>
      </div>
    </section>
  );
}
