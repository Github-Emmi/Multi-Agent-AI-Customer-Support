"use client";
import { useState, useCallback } from "react";
import toast from "react-hot-toast";
import api from "@/services/api";
import type { Ticket, CreateTicketPayload, HandoffPayload } from "@/types";

export function useTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchMyTickets = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<Ticket[]>("/tickets");
      setTickets(data);
    } catch {
      // Silently fail — user may not have tickets yet
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createTicket = useCallback(
    async (payload: CreateTicketPayload): Promise<string | null> => {
      try {
        const { data } = await api.post<{ ticket_id: string; message: string }>(
          "/tickets",
          payload
        );
        toast.success(`Ticket ${data.ticket_id} created`);
        return data.ticket_id;
      } catch {
        toast.error("Failed to create support ticket");
        return null;
      }
    },
    []
  );

  const requestHandoff = useCallback(
    async (payload: HandoffPayload): Promise<string | null> => {
      try {
        const { data } = await api.post<{ ticket_id: string; message: string }>(
          "/tickets/handoff",
          payload
        );
        toast.success(data.message);
        return data.ticket_id;
      } catch {
        toast.error("Failed to request human agent");
        return null;
      }
    },
    []
  );

  return { tickets, isLoading, fetchMyTickets, createTicket, requestHandoff };
}
