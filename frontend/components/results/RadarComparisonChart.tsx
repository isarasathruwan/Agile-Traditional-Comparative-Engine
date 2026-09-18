import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  Tooltip,
} from "recharts";
import { useEffect, useRef, useState } from "react";

interface RadarComparisonChartProps {
  dimensions: string[];
  project: number[];
  agile: number[];
  traditional: number[];
  compact?: boolean;
}

const DECISION_SIGNAL_LABELS: Record<string, string> = {
  timeline_adherence: "Timeline constraints",
  budget_accuracy: "Budget constraints",
  product_quality: "Quality assurance",
  user_satisfaction: "User feedback need",
  communication_effectiveness: "Collaboration readiness",
  security_integration: "Security and assurance",
  system_integration_effectiveness: "Integration and dependencies",
};

export default function RadarComparisonChart({
  dimensions,
  project,
  agile,
  traditional,
  compact = false,
}: RadarComparisonChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [chartSize, setChartSize] = useState({ width: 0, height: 0 });
  const data = dimensions.map((dimension, index) => ({
    dimension: DECISION_SIGNAL_LABELS[dimension] ?? dimension,
    Project: project[index],
    Agile: agile[index],
    Traditional: traditional[index],
  }));

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

  return (
    <section className={compact ? "h-full min-h-0" : "border-y border-slate-300 bg-white py-6"}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-800">Dimension Comparison</h3>
        <div className="flex items-center gap-4 text-xs font-medium">
          <span className="flex items-center gap-2 text-blue-700">
            <span className="h-2 w-2 rounded-full bg-blue-600" aria-hidden="true" />
            Project
          </span>
          <span className="flex items-center gap-2 text-teal-700">
            <span className="h-2 w-2 rounded-full bg-teal-700" aria-hidden="true" />
            Agile
          </span>
          <span className="flex items-center gap-2 text-slate-700">
            <span className="h-2 w-2 rounded-full bg-slate-500" aria-hidden="true" />
            Traditional
          </span>
        </div>
      </div>
      <p className="mb-3 text-sm text-slate-500">
        Project profile compared with Agile and Traditional reference profiles.
      </p>
      <div ref={chartContainerRef} className={compact ? "h-[calc(100%-4.5rem)] min-h-44 w-full" : "h-80 w-full"}>
        {chartSize.width > 0 && chartSize.height > 0 ? (
          <RadarChart width={chartSize.width} height={chartSize.height} data={data} outerRadius={compact ? "64%" : "70%"}>
            <PolarGrid stroke="#cbd5e1" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fill: "#334155", fontSize: 12 }}
            />
            <Tooltip />
            <Radar
              name="Project"
              dataKey="Project"
              stroke="#059669"
              fill="#059669"
              fillOpacity={0.16}
            />
            <Radar
              name="Agile"
              dataKey="Agile"
              stroke="#0f766e"
              fill="#0f766e"
              fillOpacity={0.2}
            />
            <Radar
              name="Traditional"
              dataKey="Traditional"
              stroke="#64748b"
              fill="#64748b"
              fillOpacity={0.2}
            />
          </RadarChart>
        ) : <div className="h-full animate-pulse bg-slate-100 motion-reduce:animate-none" />}
      </div>
    </section>
  );
}
