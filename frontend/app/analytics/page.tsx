"use client";
import { RefreshCw, Ticket } from "lucide-react";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/analytics/StatCard";
import { ConversationChart } from "@/components/analytics/ConversationChart";
import { AgentUsageChart } from "@/components/analytics/AgentUsageChart";
import { SatisfactionChart } from "@/components/analytics/SatisfactionChart";
import { ResponseTimeChart } from "@/components/analytics/ResponseTimeChart";
import { useAnalytics } from "@/hooks/useAnalytics";

function AnalyticsContent() {
  const {
    summary, agentUsage, dailyData,
    satisfaction, ticketStats,
    isLoading, error, refetch,
  } = useAnalytics();

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden bg-slate-50">
        <Header title="Analytics Dashboard" />

        <div className="flex h-10 items-center justify-end border-b border-slate-100 bg-white px-5">
          <Button
            variant="ghost"
            size="sm"
            onClick={refetch}
            isLoading={isLoading}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
            aria-label="Refresh analytics"
          >
            Refresh
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {isLoading && !summary ? (
            <div className="flex justify-center pt-10">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="rounded-xl bg-rose-50 p-5 text-sm text-rose-700">{error}</div>
          ) : (
            <div className="flex flex-col gap-5 max-w-5xl">
              {/* KPI row */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <StatCard
                  label="Total Conversations"
                  value={summary?.total_conversations ?? 0}
                />
                <StatCard
                  label="Avg Response Time"
                  value={summary ? `${(summary.avg_response_time_ms / 1000).toFixed(1)}s` : "—"}
                  sub="Target: < 3s"
                />
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                <ConversationChart data={dailyData} />
                <AgentUsageChart data={agentUsage} />
                <ResponseTimeChart avgMs={summary?.avg_response_time_ms ?? 0} />
                <SatisfactionChart score={summary?.satisfaction_score ?? 0} />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <ProtectedRoute>
      <AnalyticsContent />
    </ProtectedRoute>
  );
}
