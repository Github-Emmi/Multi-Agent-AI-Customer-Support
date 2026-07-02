"use client";
import { LogOut, User, Settings } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

interface HeaderProps {
  title?: string;
  sessionId?: string;
}

export function Header({ title, sessionId }: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-100 bg-white px-5">
      {/* Left — page title */}
      <div className="flex items-center gap-3 min-w-0">
        <h1 className="text-sm font-semibold text-slate-700 truncate">
          {title ?? "TechMart Support"}
        </h1>
        {sessionId && (
          <span className="hidden sm:inline text-xs font-mono text-slate-400 bg-slate-50 px-2 py-0.5 rounded">
            {sessionId}
          </span>
        )}
      </div>

      {/* Right — user actions */}
      <div className="flex items-center gap-1">
        {user?.role === "admin" && (
          <Link
            href="/admin"
            className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
            aria-label="Admin panel"
          >
            <Settings className="h-4 w-4" />
          </Link>
        )}
        <div className="flex items-center gap-2 rounded-lg px-2 py-1">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100">
            <User className="h-3.5 w-3.5 text-blue-600" aria-hidden="true" />
          </div>
          <span className="hidden sm:inline text-xs font-medium text-slate-700">
            {user?.name}
          </span>
        </div>
        <button
          onClick={logout}
          className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-rose-600 transition-colors"
          aria-label="Log out"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
