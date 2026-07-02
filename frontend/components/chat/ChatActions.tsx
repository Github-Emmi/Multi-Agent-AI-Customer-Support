"use client";
import { useState } from "react";
import { UserCheck, Mic, MicOff, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { useTickets } from "@/hooks/useTickets";
import type { RecordingState } from "@/hooks/useVoice";

// ── Handoff Button ────────────────────────────────────────────────────────────

interface HandoffButtonProps {
  sessionId: string;
}

export function HandoffButton({ sessionId }: HandoffButtonProps) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const { requestHandoff } = useTickets();

  const handleSubmit = async () => {
    setLoading(true);
    await requestHandoff({ session_id: sessionId, reason: reason || undefined });
    setLoading(false);
    setOpen(false);
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs text-slate-500
          hover:bg-slate-100 hover:text-slate-800 transition-colors"
        aria-label="Request human agent"
      >
        <UserCheck className="h-3.5 w-3.5" aria-hidden="true" />
        Human agent
      </button>

      <Modal isOpen={open} onClose={() => setOpen(false)} title="Request Human Agent" size="sm">
        <p className="mb-3 text-sm text-slate-600">
          A TechMart agent will contact you within 1 hour.
        </p>
        <Input
          label="Reason (optional)"
          placeholder="Describe what you need help with"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button size="sm" isLoading={loading} onClick={handleSubmit}>
            Request Agent
          </Button>
        </div>
      </Modal>
    </>
  );
}

// ── Voice Button ──────────────────────────────────────────────────────────────

interface VoiceButtonProps {
  recordingState: RecordingState;
  onStart: () => void;
  onStop: () => void;
}

export function VoiceButton({ recordingState, onStart, onStop }: VoiceButtonProps) {
  const isRecording = recordingState === "recording";
  const isProcessing = recordingState === "processing";

  return (
    <button
      onClick={isRecording ? onStop : onStart}
      disabled={isProcessing}
      className={`flex items-center justify-center rounded-lg p-2 transition-colors
        ${isRecording
          ? "bg-rose-100 text-rose-600 hover:bg-rose-200 animate-pulse"
          : "text-slate-400 hover:bg-slate-100 hover:text-slate-700"
        } disabled:cursor-not-allowed`}
      aria-label={isRecording ? "Stop recording" : "Start voice input"}
    >
      {isProcessing ? (
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      ) : isRecording ? (
        <MicOff className="h-4 w-4" aria-hidden="true" />
      ) : (
        <Mic className="h-4 w-4" aria-hidden="true" />
      )}
    </button>
  );
}
