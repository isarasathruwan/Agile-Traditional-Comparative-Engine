import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useEffect, useRef, useState } from "react";
import { buildDecisionDrivers, chartMagnitude, type DecisionDriver } from "@/lib/resultAnalytics";

type Props = {
  dimensions: string[];
  project: number[];
  agile: number[];
  traditional: number[];
};

export default function DecisionDriverChart({ dimensions, project, agile, traditional }: Props) {
  const drivers = buildDecisionDrivers({ dimensions, project, agile, traditional });
  const magnitude = chartMagnitude(drivers);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [chartSize, setChartSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const container = chartContainerRef.current;
    if (!container) return;

    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setChartSize({ width: Math.round(width), height: Math.round(height) });
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  if (!drivers.length) {
    return (
      <section className="border-y border-slate-200 py-8" aria-labelledby="decision-drivers-title">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Decision analysis</p>
        <h2 id="decision-drivers-title" className="mt-2 text-xl font-semibold tracking-tight text-slate-950">Decision drivers are unavailable</h2>
        <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">This result does not include a complete comparison series to visualise the project profile.</p>
      </section>
    );
  }

  return (
    <section aria-labelledby="decision-drivers-title">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-blue-700">Decision analysis</p>
          <h2 id="decision-drivers-title" className="mt-1 text-xl font-semibold tracking-tight text-slate-950">What shaped this decision</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Signals are ordered by how much closer the project is to one reference profile than the other.</p>
        </div>
        <div className="flex gap-4 text-xs font-semibold text-slate-600" aria-label="Decision driver scale">
          <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-slate-500" aria-hidden="true" />Leans Traditional</span>
          <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-blue-700" aria-hidden="true" />Leans Agile</span>
        </div>
      </div>

      <div ref={chartContainerRef} className="mt-5 h-[360px] w-full" aria-hidden="true">
        {chartSize.width > 0 && chartSize.height > 0 ? (
          <BarChart width={chartSize.width} height={chartSize.height} data={drivers} layout="vertical" margin={{ top: 2, right: 16, bottom: 2, left: 0 }}>
            <CartesianGrid horizontal={false} stroke="#e2e8f0" />
            <XAxis type="number" domain={[-magnitude, magnitude]} tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={(value: number) => value === 0 ? "Balanced" : value > 0 ? "Agile" : "Traditional"} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="label" width={148} tick={{ fill: "#334155", fontSize: 12 }} axisLine={false} tickLine={false} />
            <ReferenceLine x={0} stroke="#64748b" strokeWidth={1.5} />
            <Tooltip cursor={{ fill: "#f8fafc" }} content={<DriverTooltip />} />
            <Bar dataKey="directionalFit" radius={3} maxBarSize={24}>
              {drivers.map((driver) => <Cell key={driver.key} fill={driver.directionalFit >= 0 ? "#1d4ed8" : "#64748b"} />)}
            </Bar>
          </BarChart>
        ) : <div className="h-full animate-pulse bg-slate-100 motion-reduce:animate-none" />}
      </div>

      <p className="mt-2 text-xs leading-5 text-slate-500">The central line is balanced. Bar length indicates relative proximity to the Agile or Traditional reference profile, not a predicted project outcome.</p>
      <ul className="sr-only">
        {drivers.map((driver) => <li key={driver.key}>{driver.label}: leans {driver.preferredMethod}. Project score {driver.projectScore.toFixed(2)}, Agile reference {driver.agileReference.toFixed(2)}, Traditional reference {driver.traditionalReference.toFixed(2)}.</li>)}
      </ul>
    </section>
  );
}

function DriverTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload?: DecisionDriver }> }) {
  const driver = payload?.[0]?.payload;
  if (!active || !driver) return null;

  return (
    <div className="max-w-64 border border-slate-200 bg-white px-3 py-2.5 shadow-lg">
      <p className="text-sm font-semibold text-slate-900">{driver.label}</p>
      <p className="mt-1 text-xs font-semibold text-slate-600">Closer to {driver.preferredMethod}</p>
      <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-600">
        <dt>Project</dt><dd className="font-mono text-right text-slate-800">{driver.projectScore.toFixed(2)}</dd>
        <dt>Agile reference</dt><dd className="font-mono text-right text-slate-800">{driver.agileReference.toFixed(2)}</dd>
        <dt>Traditional reference</dt><dd className="font-mono text-right text-slate-800">{driver.traditionalReference.toFixed(2)}</dd>
      </dl>
    </div>
  );
}
