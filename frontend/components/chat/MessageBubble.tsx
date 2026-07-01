import React from "react";
import ReactMarkdown from "react-markdown";
import { AgentBadge } from "@/components/chat/AgentBadge";
import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
}

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
      role="listitem"
    >
      <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} max-w-[78%]`}>
        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed
            ${isUser
              ? "bg-blue-600 text-white rounded-br-sm"
              : "bg-white border border-slate-100 text-slate-900 rounded-bl-sm shadow-sm"
            }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose max-w-none text-slate-900 text-sm">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Agent badges + timestamp */}
        <div className="flex flex-wrap items-center gap-1 mt-1 px-1">
          {!isUser && message.agents_used && message.agents_used.length > 0 && (
            <div className="flex flex-wrap gap-1" aria-label="Agents used">
              {message.agents_used.map((agent) => (
                <AgentBadge key={agent} agent={agent} />
              ))}
            </div>
          )}
          <span className="text-xs text-slate-400">{formatTime(message.timestamp)}</span>
          {!isUser && message.response_time_ms && (
            <span className="text-xs text-slate-400">
              {(message.response_time_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
