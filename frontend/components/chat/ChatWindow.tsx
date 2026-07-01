"use client";
import React, { useEffect, useRef } from "react";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { Bot } from "lucide-react";
import type { Message } from "@/types";

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
        <Bot className="h-8 w-8 text-blue-600" aria-hidden="true" />
      </div>
      <div>
        <h2 className="text-lg font-semibold text-slate-800">
          Welcome to TechMart Support
        </h2>
        <p className="mt-1 text-sm text-slate-500 max-w-xs">
          Our AI agents are ready to help with billing, technical support,
          product questions, and more.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2 mt-2">
        {[
          "How do I get a refund?",
          "I can't log into my account",
          "What is the warranty policy?",
          "What are your business hours?",
        ].map((hint) => (
          <span
            key={hint}
            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600"
          >
            {hint}
          </span>
        ))}
      </div>
    </div>
  );
}

export function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div
      className="flex-1 overflow-y-auto bg-slate-50 px-4 py-4"
      role="log"
      aria-label="Conversation"
      aria-live="polite"
    >
      {messages.length === 0 ? (
        <WelcomeScreen />
      ) : (
        <div role="list" className="flex flex-col">
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="rounded-2xl rounded-bl-sm border border-slate-100 bg-white shadow-sm">
                <TypingIndicator />
              </div>
            </div>
          )}
        </div>
      )}
      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
}
