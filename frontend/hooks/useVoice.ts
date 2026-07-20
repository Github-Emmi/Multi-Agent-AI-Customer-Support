"use client";
import { useState, useCallback, useRef } from "react";
import toast from "react-hot-toast";
import api from "@/services/api";
import type { VoiceResponse } from "@/types";

export type RecordingState = "idle" | "recording" | "processing";

export function useVoice(
  sessionId: string,
  onResponse: (r: VoiceResponse) => void,
  onTranscriptionSuccess?: (text: string) => void
) {
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const recognitionRef = useRef<any>(null);

  const startRecording = useCallback(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      toast.error("Speech recognition is not supported in this browser. Please use Chrome or Safari.");
      return;
    }

    try {
      setRecordingState("recording");
      const recognition = new SpeechRecognition();

      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onresult = async (event: any) => {
        const transcriptText = event.results[0]?.[0]?.transcript;
        if (!transcriptText) return;

        // Optimistically render spoken text inside the UI chat feed right away
        if (onTranscriptionSuccess) {
          onTranscriptionSuccess(transcriptText);
        }

        setRecordingState("processing");

        try {
          // Send text string payload directly to backend API
          const { data } = await api.post<VoiceResponse>(
            `/voice/transcribe?session_id=${sessionId}`,
            { text: transcriptText },
            { headers: { "Content-Type": "application/json" } }
          );
          onResponse(data);
        } catch (error) {
          toast.error("Voice pipeline error. Please try typing.");
        } finally {
          setRecordingState("idle");
        }
      };

      recognition.onerror = (event: any) => {
        console.error("Speech Recognition Error:", event.error);
        if (event.error === "not-allowed") {
          toast.error("Microphone access blocked by browser settings.");
        } else {
          toast.error("Audio detection issue. Please speak again.");
        }
        setRecordingState("idle");
      };

      recognition.onend = () => {
        setRecordingState("idle");
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (error) {
      console.error("Failed to initialize speech engine:", error);
      toast.error("Failed to start voice capture.");
      setRecordingState("idle");
    }
  }, [sessionId, onResponse, onTranscriptionSuccess]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  return { recordingState, startRecording, stopRecording };
}
