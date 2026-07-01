"use client";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import type { AgentUsageItem } from "@/types";
import { AGENT_COLORS } from "@/types";

const BAR_FILL: Record<string, string> = {
  billing: "#10b981",
  technical: "#3b82f6",
  product: "#8b5cf6",
  complaint: "#f43f5e",
  faq: "#f59e0b",
};

interface AgentUsageChartProps {
  data: AgentUsageItem[];
}

export function AgentUsageChart({ data }: AgentUsageChartProps) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-slate-700">Agent Usage</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="agent" tick={{ fontSize: 11 }} stroke="#cbd5e1" />
          <YAxis tick={{ fontSize: 11 }} stroke="#cbd5e1" allowDecimals={false} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} name="Queries">
            {data.map((entry) => (
              <Cell
                key={entry.agent}
                fill={BAR_FILL[entry.agent] ?? "#94a3b8"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
