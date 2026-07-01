"use client";
import { useState } from "react";
import Link from "next/link";
import { MessageSquare, ChevronRight, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { Sidebar } from "@/components/layout/Sidebar";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { useSessions } from "@/hooks/useSessions";
import api from "@/services/api";

function HistoryContent() {
  const { sessions, isLoading, refetch } = useSessions();

  const handleDelete = async (sessionId: string) => {
    if (!confirm("Delete this conversation?")) return;
    try {
      await api.delete(`/history/${sessionId}`);
      toast.success("Conversation deleted");
      refetch();
    } catch {
      toast.error("Failed to delete conversation");
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden bg-slate-50">
        <div className="flex h-14 items-center border-b border-slate-100 bg-white px-5">
          <h1 className="text-sm font-semibold text-slate-700">Conversation History</h1>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {isLoading ? (
            <div className="flex justify-center pt-10">
              <Spinner />
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
              <MessageSquare className="h-10 w-10 text-slate-300" />
              <p className="text-sm text-slate-500">No conversations yet.</p>
              <Link href="/chat">
                <Button size="sm">Start a conversation</Button>
              </Link>
            </div>
          ) : (
            <ul className="flex flex-col gap-2 max-w-2xl" role="list">
              {sessions.map((session) => (
                <li
                  key={session.session_id}
                  className="flex items-center justify-between rounded-xl border border-slate-100 bg-white px-4 py-3 shadow-sm hover:shadow-md transition-shadow"
                >
                  <Link
                    href={`/chat?session=${session.session_id}`}
                    className="flex flex-1 items-center gap-3 min-w-0"
                  >
                    <MessageSquare className="h-4 w-4 text-blue-400 shrink-0" aria-hidden="true" />
                    <span className="truncate text-sm font-medium text-slate-800">
                      {session.title || "Untitled"}
                    </span>
                    {session.is_resolved && (
                      <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
                        Resolved
                      </span>
                    )}
                  </Link>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <ChevronRight className="h-4 w-4 text-slate-300" aria-hidden="true" />
                    <button
                      onClick={() => handleDelete(session.session_id)}
                      className="p-1 text-slate-300 hover:text-rose-500 transition-colors"
                      aria-label={`Delete conversation: ${session.title}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}

export default function HistoryPage() {
  return (
    <ProtectedRoute>
      <HistoryContent />
    </ProtectedRoute>
  );
}
