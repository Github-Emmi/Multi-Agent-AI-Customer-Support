"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Ticket, PlusCircle, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { useTickets } from "@/hooks/useTickets";
import { useSessions } from "@/hooks/useSessions";
import type { TicketStatus, TicketPriority } from "@/types";

const STATUS_COLORS: Record<TicketStatus, string> = {
  open: "bg-blue-100 text-blue-700",
  in_progress: "bg-amber-100 text-amber-700",
  resolved: "bg-emerald-100 text-emerald-700",
  closed: "bg-slate-100 text-slate-600",
};

const PRIORITY_COLORS: Record<TicketPriority, string> = {
  low: "text-slate-500",
  medium: "text-amber-600",
  high: "text-orange-600",
  urgent: "text-rose-600 font-semibold",
};

function TicketsContent() {
  const { tickets, isLoading, fetchMyTickets, createTicket } = useTickets();
  const { sessions } = useSessions();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ session_id: "", subject: "", priority: "medium" });

  useEffect(() => { fetchMyTickets(); }, [fetchMyTickets]);

  const handleCreate = async () => {
    if (!form.subject.trim()) { toast.error("Subject is required"); return; }
    const id = await createTicket({
      session_id: form.session_id || `sess_manual_${Date.now()}`,
      subject: form.subject,
      priority: form.priority as TicketPriority,
    });
    if (id) { setShowCreate(false); setForm({ session_id: "", subject: "", priority: "medium" }); fetchMyTickets(); }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden bg-slate-50">
        <Header title="My Support Tickets" />

        <div className="flex h-10 items-center justify-end border-b border-slate-100 bg-white px-5">
          <Button
            size="sm"
            leftIcon={<PlusCircle className="h-3.5 w-3.5" />}
            onClick={() => setShowCreate(true)}
          >
            New Ticket
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {isLoading ? (
            <div className="flex justify-center pt-10"><Spinner /></div>
          ) : tickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
              <Ticket className="h-10 w-10 text-slate-300" />
              <p className="text-sm text-slate-500">No support tickets yet.</p>
              <Button size="sm" onClick={() => setShowCreate(true)}>Create a ticket</Button>
            </div>
          ) : (
            <ul className="flex flex-col gap-2 max-w-2xl" role="list">
              {tickets.map((t) => (
                <li key={t.ticket_id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-mono text-slate-400">{t.ticket_id}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_COLORS[t.status as TicketStatus] ?? "bg-slate-100 text-slate-600"}`}>
                        {t.status.replace("_", " ")}
                      </span>
                    </div>
                    <p className="truncate text-sm font-medium text-slate-800">{t.subject}</p>
                    <p className={`text-xs mt-0.5 ${PRIORITY_COLORS[t.priority as TicketPriority] ?? "text-slate-500"}`}>
                      {t.priority} priority
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300 shrink-0 ml-3" />
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>

      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onConfirm={handleCreate}
        title="Create Support Ticket"
        confirmText="Create Ticket"
      >
        <div className="flex flex-col gap-3">
          <Input
            label="Subject"
            value={form.subject}
            onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
            placeholder="Describe your issue briefly"
            required
          />
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-slate-700">Priority</label>
            <select
              value={form.priority}
              onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
          {sessions.length > 0 && (
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-slate-700">Link to conversation (optional)</label>
              <select
                value={form.session_id}
                onChange={(e) => setForm((f) => ({ ...f, session_id: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">None</option>
                {sessions.slice(0, 10).map((s) => (
                  <option key={s.session_id} value={s.session_id}>
                    {s.title || s.session_id}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}

export default function TicketsPage() {
  return (
    <ProtectedRoute>
      <TicketsContent />
    </ProtectedRoute>
  );
}
