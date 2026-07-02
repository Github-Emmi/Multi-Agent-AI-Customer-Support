"use client";
import { useState, useCallback, useRef } from "react";
import toast from "react-hot-toast";
import api from "@/services/api";
import type { VoiceResponse } from "@/types";

export type RecordingState = "idle" | "recording" | "processing";

export function useVoice(sessionId: string, onResponse: (r: VoiceResponse) => void) {
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      toast.error("Microphone not supported in this browser");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setRecordingState("processing");
        try {
          const formData = new FormData();
          formData.append("audio", blob, "recording.webm");
          const { data } = await api.post<VoiceResponse>(
            `/voice/transcribe?session_id=${sessionId}`,
            formData,
            { headers: { "Content-Type": "multipart/form-data" } }
          );
          onResponse(data);
        } catch {
          toast.error("Voice transcription failed. Please try typing.");
        } finally {
          setRecordingState("idle");
        }
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecordingState("recording");
    } catch {
      toast.error("Microphone access denied");
    }
  }, [sessionId, onResponse]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  return { recordingState, startRecording, stopRecording };
}
