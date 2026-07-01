"use client";
import { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";
import { Button } from "@/components/ui/Button";
import api from "@/services/api";

export function FileUpload({ onUpload }: { onUpload: () => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      toast.error("Only PDF files are accepted");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      toast.error("File exceeds 20 MB limit");
      return;
    }
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      await api.post("/admin/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(`${file.name} uploaded successfully`);
      onUpload();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Upload failed";
      toast.error(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed
        p-8 text-center transition-colors cursor-pointer
        ${isDragging ? "border-blue-400 bg-blue-50" : "border-slate-200 hover:border-slate-300"}`}
      onClick={() => inputRef.current?.click()}
      role="button"
      aria-label="Upload PDF document"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") inputRef.current?.click(); }}
    >
      <Upload className="mb-3 h-8 w-8 text-slate-400" aria-hidden="true" />
      <p className="text-sm font-medium text-slate-700">
        Drop a PDF here or click to upload
      </p>
      <p className="mt-1 text-xs text-slate-400">PDF only · Max 20 MB</p>
      {isUploading && (
        <p className="mt-2 text-xs text-blue-600">Uploading…</p>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) uploadFile(file);
        }}
        aria-label="File input"
      />
    </div>
  );
}
