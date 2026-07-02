"use client";
import React, { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface MessageInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  className?: string;
}

export function MessageInput({ onSend, isLoading, disabled, className = "" }: MessageInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-slate-100 bg-white px-4 py-3">
      <div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-400 transition-all">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message… (Enter to send, Shift+Enter for new line)"
          rows={1}
          disabled={isLoading || disabled}
          aria-label="Message input"
          className="flex-1 resize-none bg-transparent text-sm text-slate-900 placeholder:text-slate-400
            focus:outline-none disabled:cursor-not-allowed"
        />
        <Button
          variant="primary"
          size="sm"
          onClick={handleSend}
          disabled={!value.trim() || isLoading || disabled}
          isLoading={isLoading}
          aria-label="Send message"
          className="shrink-0 rounded-lg p-2"
        >
          {!isLoading && <Send className="h-4 w-4" />}
        </Button>
      </div>
      <p className="mt-1 text-center text-xs text-slate-400">
        TechMart AI may make mistakes. Verify important information.
      </p>
    </div>
  );
}
