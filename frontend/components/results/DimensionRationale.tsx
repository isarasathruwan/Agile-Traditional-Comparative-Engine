interface DimensionRationaleProps {
  dimensions: string[];
  project: number[];
  agile: number[];
  traditional: number[];
}

function formatLabel(raw: string): string {
  return raw
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function DimensionRationale({
  dimensions,
  project,
  agile,
  traditional,
}: DimensionRationaleProps) {
  if (!dimensions.length || !project.length || !agile.length || !traditional.length) {
    return null;
  }

  return (
    <section className="border-b border-slate-300 bg-white py-6">
      <h3 className="text-base font-semibold text-slate-800">Why This Recommendation</h3>
      <p className="mt-1 text-sm text-slate-500">
        Each project dimension is compared against Agile and Traditional reference profiles.
      </p>
      <div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">
        {dimensions.map((dimension, index) => {
          const projectScore = project[index] ?? 0;
          const agileScore = agile[index] ?? 0;
          const traditionalScore = traditional[index] ?? 0;
          const agileGap = Math.abs(projectScore - agileScore);
          const traditionalGap = Math.abs(projectScore - traditionalScore);
          const closer = agileGap <= traditionalGap ? "Agile" : "Traditional";
          return (
            <div key={dimension} className="py-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-700">{formatLabel(dimension)}</p>
                <span
                  className={[
                    "rounded-full px-2 py-0.5 text-xs font-semibold",
                    closer === "Agile"
                      ? "bg-teal-50 text-teal-800"
                      : "bg-slate-200 text-slate-700",
                  ].join(" ")}
                >
                  Closer to {closer}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-600">
                Project score {projectScore.toFixed(2)} | Agile reference {agileScore.toFixed(2)} | Traditional reference{" "}
                {traditionalScore.toFixed(2)}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
