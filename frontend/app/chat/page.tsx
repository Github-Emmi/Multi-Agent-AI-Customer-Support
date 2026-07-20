"use client";
import { useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { PlusCircle } from "lucide-react";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { MessageInput } from "@/components/chat/MessageInput";
import { SatisfactionWidget } from "@/components/chat/SatisfactionWidget";
import { HandoffButton, VoiceButton } from "@/components/chat/ChatActions";
import { useChat } from "@/hooks/useChat";
import { useVoice } from "@/hooks/useVoice";
import type { VoiceResponse } from "@/types";

function ChatPageContent() {
  const searchParams = useSearchParams();
  const sessionParam = searchParams?.get("session") ?? undefined;
  const { messages, sendMessage, appendMessages, isLoading, sessionId, resetSession } =
    useChat(sessionParam);

  // As soon as the browser transcribes speech, show the user's message.
  const handleTranscription = useCallback(
    (text: string) => {
      appendMessages({
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      });
    },
    [appendMessages]
  );

  // The /voice/transcribe endpoint already executed the full agent pipeline
  // and persisted both turns. Append ONLY the assistant reply — do NOT call
  // /chat again (that would double-run the pipeline and drop this response).
  const handleVoiceResponse = useCallback(
    (r: VoiceResponse) => {
      appendMessages({
        role: "assistant",
        content: r.response,
        agents_used: r.agents_used,
        response_time_ms: r.response_time_ms,
        timestamp: new Date().toISOString(),
      });
    },
    [appendMessages]
  );

  const { recordingState, startRecording, stopRecording } = useVoice(
    sessionId,
    handleVoiceResponse,
    handleTranscription
  );

  const hasMessages = messages.length > 0;
  const sessionTitle =
    messages.length > 0 ? messages[0].content.slice(0, 50) : "New conversation";

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <Header title={sessionTitle} sessionId={sessionId} />

        {/* Chat actions toolbar */}
        <div className="flex items-center gap-2 border-b border-slate-100 bg-white px-4 py-1.5">
          <HandoffButton sessionId={sessionId} />
          <button
            onClick={resetSession}
            className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs
              text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors ml-auto"
            aria-label="New conversation"
          >
            <PlusCircle className="h-3.5 w-3.5" aria-hidden="true" />
            New chat
          </button>
        </div>

        {/* Messages */}
        <ChatWindow messages={messages} isLoading={isLoading} />

        {/* Satisfaction widget — shown after first assistant response */}
        {hasMessages && messages[messages.length - 1]?.role === "assistant" && (
          <SatisfactionWidget sessionId={sessionId} />
        )}

        {/* Input bar with voice button */}
        <div className="border-t border-slate-100 bg-white px-4 py-3">
          <div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-slate-50
            px-3 py-1 focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-400
            transition-all">
            <VoiceButton
              recordingState={recordingState}
              onStart={startRecording}
              onStop={stopRecording}
            />
            <MessageInput
              onSend={sendMessage}
              isLoading={isLoading}
            />
          </div>
          <p className="mt-1 text-center text-xs text-slate-400">
            TechMart AI may make mistakes. Verify important information.
          </p>
        </div>
      </main>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatPageContent />
    </ProtectedRoute>
  );
}
