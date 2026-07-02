"use client";
import { useState, useEffect, useCallback } from "react";
import { RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { FileUpload } from "@/components/admin/FileUpload";
import { DocumentList } from "@/components/admin/DocumentList";
import api from "@/services/api";
import type { KBDocument } from "@/types";

function AdminContent() {
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<KBDocument[]>("/admin/documents");
      setDocuments(data);
    } catch {
      toast.error("Failed to load documents");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  const handleReindex = async () => {
    setIsReindexing(true);
    try {
      await api.post("/admin/reindex");
      toast.success("Knowledge base re-indexed successfully");
      fetchDocuments();
    } catch {
      toast.error("Re-indexing failed");
    } finally {
      setIsReindexing(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden bg-slate-50">
        <Header title="Knowledge Base Admin" />

        {/* Re-index toolbar */}
        <div className="flex h-10 items-center justify-end border-b border-slate-100 bg-white px-5">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleReindex}
            isLoading={isReindexing}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Re-index All
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 max-w-2xl w-full mx-auto">
          <section className="mb-6">
            <h2 className="mb-3 text-sm font-semibold text-slate-700">
              Upload Document
            </h2>
            <FileUpload onUpload={fetchDocuments} />
          </section>

          <section>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">
              Indexed Documents ({documents.length})
            </h2>
            {isLoading ? (
              <div className="flex justify-center py-6">
                <Spinner />
              </div>
            ) : (
              <DocumentList documents={documents} onRefresh={fetchDocuments} />
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute requireAdmin>
      <AdminContent />
    </ProtectedRoute>
  );
}
