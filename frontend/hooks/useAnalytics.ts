"use client";
import { useState, useEffect, useCallback } from "react";
import api from "@/services/api";
import type { AnalyticsSummary, AgentUsageItem, DailyConversation } from "@/types";

export function useAnalytics() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [agentUsage, setAgentUsage] = useState<AgentUsageItem[]>([]);
  const [dailyData, setDailyData] = useState<DailyConversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryRes, usageRes, dailyRes] = await Promise.all([
        api.get<AnalyticsSummary>("/analytics/summary"),
        api.get<AgentUsageItem[]>("/analytics/agent-usage"),
        api.get<DailyConversation[]>("/analytics/daily"),
      ]);
      setSummary(summaryRes.data);
      setAgentUsage(usageRes.data);
      setDailyData(dailyRes.data);
    } catch {
      setError("Failed to load analytics data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return { summary, agentUsage, dailyData, isLoading, error, refetch: fetchAll };
}
