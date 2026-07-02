"use client";
import { useState, useEffect, useCallback } from "react";
import api from "@/services/api";
import type {
  AnalyticsSummary,
  AgentUsageItem,
  DailyConversation,
  SatisfactionDistribution,
  SentimentTrend,
  TicketStats,
} from "@/types";

export function useAnalytics() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [agentUsage, setAgentUsage] = useState<AgentUsageItem[]>([]);
  const [dailyData, setDailyData] = useState<DailyConversation[]>([]);
  const [satisfaction, setSatisfaction] = useState<SatisfactionDistribution | null>(null);
  const [sentimentTrends, setSentimentTrends] = useState<SentimentTrend[]>([]);
  const [ticketStats, setTicketStats] = useState<TicketStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryRes, usageRes, dailyRes, satRes, sentRes, ticketRes] =
        await Promise.allSettled([
          api.get<AnalyticsSummary>("/analytics/summary"),
          api.get<AgentUsageItem[]>("/analytics/agent-usage"),
          api.get<DailyConversation[]>("/analytics/daily"),
          api.get<SatisfactionDistribution>("/analytics/satisfaction"),
          api.get<SentimentTrend[]>("/analytics/sentiment"),
          api.get<TicketStats>("/analytics/tickets"),
        ]);

      if (summaryRes.status === "fulfilled") setSummary(summaryRes.value.data);
      if (usageRes.status === "fulfilled") setAgentUsage(usageRes.value.data);
      if (dailyRes.status === "fulfilled") setDailyData(dailyRes.value.data);
      if (satRes.status === "fulfilled") setSatisfaction(satRes.value.data);
      if (sentRes.status === "fulfilled") setSentimentTrends(sentRes.value.data);
      if (ticketRes.status === "fulfilled") setTicketStats(ticketRes.value.data);
    } catch {
      setError("Failed to load analytics data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    summary,
    agentUsage,
    dailyData,
    satisfaction,
    sentimentTrends,
    ticketStats,
    isLoading,
    error,
    refetch: fetchAll,
  };
}
