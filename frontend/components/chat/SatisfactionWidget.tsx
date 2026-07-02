"use client";
import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import toast from "react-hot-toast";
import api from "@/services/api";

interface SatisfactionWidgetProps {
  sessionId: string;
}

export function SatisfactionWidget({ sessionId }: SatisfactionWidgetProps) {
  const [rated, setRated] = useState<"positive" | "negative" | null>(null);

  const submit = async (rating: number) => {
    try {
      await api.post("/analytics/feedback", { session_id: sessionId, rating });
      setRated(rating >= 4 ? "positive" : "negative");
      toast.success("Thank you for your feedback!");
    } catch {
      toast.error("Could not save feedback");
    }
  };

  if (rated) {
    return (
      <div className="flex items-center justify-center gap-2 py-2 text-xs text-slate-400">
        {rated === "positive" ? (
          <ThumbsUp className="h-3.5 w-3.5 text-emerald-500" />
        ) : (
          <ThumbsDown className="h-3.5 w-3.5 text-rose-400" />
        )}
        Feedback recorded
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center gap-3 border-t border-slate-100 py-2">
      <span className="text-xs text-slate-400">Was this helpful?</span>
      <button
        onClick={() => submit(5)}
        className="rounded p-1 text-slate-400 hover:text-emerald-600 transition-colors"
        aria-label="Helpful"
      >
        <ThumbsUp className="h-4 w-4" />
      </button>
      <button
        onClick={() => submit(1)}
        className="rounded p-1 text-slate-400 hover:text-rose-500 transition-colors"
        aria-label="Not helpful"
      >
        <ThumbsDown className="h-4 w-4" />
      </button>
    </div>
  );
}
