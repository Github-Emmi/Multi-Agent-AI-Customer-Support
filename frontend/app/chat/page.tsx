"use client";
import { useSearchParams } from "next/navigation";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { MessageInput } from "@/components/chat/MessageInput";
import { useChat } from "@/hooks/useChat";

function ChatPageContent() {
  const searchParams = useSearchParams();
  const sessionParam = searchParams.get("session") ?? undefined;
  const { messages, sendMessage, isLoading, sessionId } = useChat(sessionParam);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <div className="flex h-14 items-center border-b border-slate-100 bg-white px-5">
          <h1 className="text-sm font-semibold text-slate-700">
            New conversation
          </h1>
          <span className="ml-auto text-xs text-slate-400 font-mono">{sessionId}</span>
        </div>

        {/* Messages */}
        <ChatWindow messages={messages} isLoading={isLoading} />

        {/* Input */}
        <MessageInput onSend={sendMessage} isLoading={isLoading} />
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
