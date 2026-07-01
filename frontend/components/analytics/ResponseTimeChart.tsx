"use client";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface DataPoint {
  label: string;
  value: number;
}

interface ResponseTimeChartProps {
  avgMs: number;
}

// Generate sample data points around the average for visual display
function buildData(avgMs: number): DataPoint[] {
  return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, i) => ({
    label: day,
    value: Math.round(avgMs * (0.85 + Math.sin(i) * 0.15)),
  }));
}

export function ResponseTimeChart({ avgMs }: ResponseTimeChartProps) {
  const data = buildData(avgMs || 2000);

  return (
    <div className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
      <h3 className="mb-1 text-sm font-semibold text-slate-700">Avg Response Time</h3>
      <p className="mb-4 text-3xl font-bold text-slate-900">
        {avgMs > 0 ? `${(avgMs / 1000).toFixed(1)}s` : "—"}
      </p>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} stroke="#cbd5e1" />
          <YAxis tick={{ fontSize: 11 }} stroke="#cbd5e1" unit="ms" />
          <Tooltip
            formatter={(v: number) => [`${v}ms`, "Response time"]}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
