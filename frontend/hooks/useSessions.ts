"use client";
import { useState, useEffect, useCallback } from "react";
import api from "@/services/api";
import type { Session } from "@/types";

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<Session[]>("/chat/sessions");
      setSessions(data);
    } catch {
      // Silently fail — user may not have sessions yet
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return { sessions, isLoading, refetch: fetchSessions };
}
