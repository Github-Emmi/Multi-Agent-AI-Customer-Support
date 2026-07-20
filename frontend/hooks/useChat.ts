"use client";
import { useState, useCallback, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import toast from "react-hot-toast";
import api from "@/services/api";
import type { Message, ChatResponse } from "@/types";

export function useChat(initialSessionId?: string) {
  const [sessionId, setSessionId] = useState<string>(
    initialSessionId ?? `sess_${uuidv4().replace(/-/g, "").slice(0, 12)}`,
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load history for existing session
  useEffect(() => {
    if (!initialSessionId) return;
    api
      .get(`/history/${initialSessionId}`)
      .then(({ data }) => {
        if (data.turns?.length) setMessages(data.turns);
      })
      .catch(() => {});
  }, [initialSessionId]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      const userMsg: Message = {
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const { data } = await api.post<ChatResponse>("/chat", {
          session_id: sessionId,
          message: text,
        });

        console.log("Received data from /chat:", data);

        const assistantMsg: Message = {
          role: "assistant",
          content: data.response,
          agents_used: data.agents_used,
          response_time_ms: data.response_time_ms,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        toast.error("Failed to send message. Please try again.");
        // Remove optimistic user message on failure
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId],
  );

  const resetSession = useCallback(() => {
    const newId = `sess_${uuidv4().replace(/-/g, "").slice(0, 12)}`;
    setSessionId(newId);
    setMessages([]);
  }, []);

  // Append pre-built messages directly to the feed WITHOUT calling /chat.
  // Used by the voice flow: /voice/transcribe already ran the full agent
  // pipeline and persisted both turns server-side, so we must not re-run it.
  const appendMessages = useCallback((...msgs: Message[]) => {
    if (msgs.length === 0) return;
    setMessages((prev) => [...prev, ...msgs]);
  }, []);

  return {
    messages,
    sendMessage,
    appendMessages,
    isLoading,
    sessionId,
    resetSession,
  };
}
