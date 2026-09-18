import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface CompositeBarChartProps {
  agileScore: number;
  traditionalScore: number;
}

export default function CompositeBarChart({
  agileScore,
  traditionalScore,
}: CompositeBarChartProps) {
  const data = [
    { methodology: "Agile", score: agileScore, fill: "#1d4ed8" },
    { methodology: "Traditional", score: traditionalScore, fill: "#64748b" },
  ];

  return (
    <section className="border-b border-slate-300 bg-white py-6">
      <h3 className="text-base font-semibold text-slate-800">Composite Scores</h3>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="methodology" tick={{ fill: "#475569" }} />
            <YAxis domain={[0, 100]} tick={{ fill: "#475569" }} />
            <Tooltip />
            <Bar dataKey="score" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
