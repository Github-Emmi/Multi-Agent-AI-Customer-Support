"use client";
import { ResponsiveContainer, PieChart, Pie, Cell, Legend, Tooltip } from "recharts";

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#f43f5e", "#8b5cf6"];
const LABELS = ["1 star", "2 stars", "3 stars", "4 stars", "5 stars"];

interface SatisfactionChartProps {
  score: number; // 0-5 average
}

export function SatisfactionChart({ score }: SatisfactionChartProps) {
  // Build a distribution from the average score (simplified visual)
  const filledStars = Math.round(score);
  const data = LABELS.map((label, i) => ({
    name: label,
    value: i + 1 === filledStars ? 60 : Math.max(5, 20 - Math.abs(i + 1 - filledStars) * 8),
  }));

  return (
    <div className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
      <h3 className="mb-1 text-sm font-semibold text-slate-700">Satisfaction Score</h3>
      <p className="mb-4 text-3xl font-bold text-slate-900">
        {score > 0 ? score.toFixed(1) : "—"}
        <span className="ml-1 text-sm font-normal text-slate-400">/ 5</span>
      </p>
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={75}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
          />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
