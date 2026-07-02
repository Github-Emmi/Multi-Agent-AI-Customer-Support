"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LogOut,
  BarChart2,
  Settings,
  MessageSquare,
  History,
  Ticket,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useSessions } from "@/hooks/useSessions";
import type { Session } from "@/types";

interface NavItemProps {
  href: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
}

function NavItem({ href, icon, label, active }: NavItemProps) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors
        ${
          active
            ? "bg-blue-50 text-blue-700"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
        }`}
      aria-current={active ? "page" : undefined}
    >
      <span aria-hidden="true">{icon}</span>
      {label}
    </Link>
  );
}

interface SessionItemProps {
  session: Session;
  active: boolean;
}

function SessionItem({ session, active }: SessionItemProps) {
  return (
    <Link
      href={`/chat?session=${session.session_id}`}
      className={`block rounded-lg px-3 py-2 text-xs transition-colors truncate
        ${
          active
            ? "bg-blue-50 text-blue-700 font-medium"
            : "text-slate-600 hover:bg-slate-100"
        }`}
      title={session.title}
    >
      {session.title || "Untitled conversation"}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { sessions } = useSessions();

  const searchParams =
    typeof window !== "undefined"
      ? new URLSearchParams(window.location.search)
      : null;
  const activeSession = searchParams?.get("session");

  return (
    <aside className="flex h-full w-64 flex-col border-r border-slate-200 bg-white">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b border-slate-100 px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-600">
          <span className="text-xs font-bold text-white">TM</span>
        </div>
        <span className="font-semibold text-slate-800 text-sm">
          TechMart Support
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 p-3" aria-label="Main navigation">
        <NavItem
          href="/chat"
          icon={<MessageSquare className="h-4 w-4" />}
          label="Chat"
          active={pathname === "/chat"}
        />
        <NavItem
          href="/history"
          icon={<History className="h-4 w-4" />}
          label="History"
          active={pathname === "/history"}
        />
        <NavItem
          href="/tickets"
          icon={<Ticket className="h-4 w-4" />}
          label="Tickets"
          active={pathname === "/tickets"}
        />
        <NavItem
          href="/analytics"
          icon={<BarChart2 className="h-4 w-4" />}
          label="Analytics"
          active={pathname === "/analytics"}
        />
        {user?.role === "admin" && (
          <NavItem
            href="/admin"
            icon={<Settings className="h-4 w-4" />}
            label="Admin"
            active={pathname === "/admin"}
          />
        )}
      </nav>

      {/* Recent sessions */}
      {sessions.length > 0 && (
        <div className="flex-1 overflow-y-auto px-3 pb-2">
          <p className="mb-1.5 px-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Recent
          </p>
          <div className="flex flex-col gap-0.5">
            {sessions.slice(0, 10).map((s) => (
              <SessionItem
                key={s.session_id}
                session={s}
                active={activeSession === s.session_id}
              />
            ))}
          </div>
        </div>
      )}

      {/* User footer */}
      <div className="border-t border-slate-100 p-3">
        <div className="flex items-center justify-between rounded-lg px-2 py-1.5">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-800">
              {user?.name}
            </p>
            <p className="truncate text-xs text-slate-400">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
            aria-label="Log out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
