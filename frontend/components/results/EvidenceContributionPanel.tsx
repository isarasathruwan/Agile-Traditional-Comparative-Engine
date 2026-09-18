import { averageEvidenceCoverage, buildEvidenceContributions } from "@/lib/resultAnalytics";

type Props = {
  confirmedItemCount: number;
  documentEvidenceCap: number;
  documentCoverage: Record<string, number>;
  documentContribution: Record<string, number>;
  onReviewEvidence: () => void;
};

export default function EvidenceContributionPanel({
  confirmedItemCount,
  documentEvidenceCap,
  documentCoverage,
  documentContribution,
  onReviewEvidence,
}: Props) {
  const contributions = buildEvidenceContributions({ coverage: documentCoverage, contribution: documentContribution });
  const averageCoverage = averageEvidenceCoverage(contributions);

  return (
    <section aria-labelledby="evidence-contribution-title" className="mt-5 border-y border-blue-100 bg-blue-50/50 px-0 py-4 sm:px-4">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-blue-700">Assessment basis</p>
          <h2 id="evidence-contribution-title" className="mt-1 text-base font-semibold text-slate-950">Confirmed document evidence</h2>
          <p className="mt-1 max-w-xl text-sm leading-6 text-slate-700">{confirmedItemCount} cited document-only signal{confirmedItemCount === 1 ? " was" : "s were"} confirmed. Each construct can receive up to {(documentEvidenceCap * 100).toFixed(0)}% document contribution.</p>
        </div>
        <div className="shrink-0 sm:text-right">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Average coverage</p>
          <p className="mt-1 font-mono text-2xl font-semibold text-slate-950">{Math.round(averageCoverage * 100)}%</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {contributions.map((item) => (
          <div key={item.key} className="border-t border-blue-100 pt-3">
            <div className="flex items-center justify-between gap-2 text-xs font-semibold text-slate-700"><span>{item.label}</span><span className="font-mono">{Math.round(item.coverage * 100)}%</span></div>
            <div className="mt-2 h-1.5 bg-blue-100" role="img" aria-label={`${item.label} document evidence coverage ${Math.round(item.coverage * 100)} percent, contributing ${Math.round(item.contribution * 100)} percent of the construct score`}>
              <div className="h-full bg-blue-700" style={{ width: `${item.coverage * 100}%` }} />
            </div>
            <p className="mt-1.5 text-xs text-slate-600">{Math.round(item.contribution * 100)}% score contribution</p>
          </div>
        ))}
      </div>

      <button type="button" onClick={onReviewEvidence} className="mt-4 text-sm font-semibold text-blue-700 transition-colors hover:text-blue-900 active:translate-y-px">Review cited evidence</button>
    </section>
  );
}
