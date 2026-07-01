import { TrendingUp } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
}

export function StatCard({ label, value, sub }: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <p className="text-sm text-slate-500">{label}</p>
        <TrendingUp className="h-4 w-4 text-blue-400" aria-hidden="true" />
      </div>
      <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}
