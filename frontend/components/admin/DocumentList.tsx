"use client";
import { FileText, CheckCircle, Clock, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { Button } from "@/components/ui/Button";
import api from "@/services/api";
import type { KBDocument } from "@/types";

interface DocumentListProps {
  documents: KBDocument[];
  onRefresh: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentList({ documents, onRefresh }: DocumentListProps) {
  const handleDelete = async (filename: string) => {
    if (!confirm(`Delete ${filename} from the knowledge base?`)) return;
    try {
      await api.delete(`/admin/documents/${encodeURIComponent(filename)}`);
      toast.success(`${filename} deleted and index updated`);
      onRefresh();
    } catch {
      toast.error("Failed to delete document");
    }
  };

  if (!documents.length) {
    return (
      <p className="text-sm text-slate-500 text-center py-6">
        No documents in the knowledge base yet.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-2" role="list" aria-label="Knowledge base documents">
      {documents.map((doc) => (
        <li
          key={doc.filename}
          className="flex items-center justify-between rounded-lg border border-slate-100 bg-white px-4 py-3"
        >
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-slate-400 shrink-0" aria-hidden="true" />
            <div>
              <p className="text-sm font-medium text-slate-800">{doc.filename}</p>
              <p className="text-xs text-slate-400">{formatBytes(doc.file_size_bytes)}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {doc.is_indexed ? (
              <span className="flex items-center gap-1 text-xs text-emerald-600">
                <CheckCircle className="h-3.5 w-3.5" aria-hidden="true" />
                Indexed
              </span>
            ) : (
              <span className="flex items-center gap-1 text-xs text-amber-600">
                <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                Pending
              </span>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDelete(doc.filename)}
              aria-label={`Delete ${doc.filename}`}
              className="p-1 text-slate-400 hover:text-rose-600"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </li>
      ))}
    </ul>
  );
}
