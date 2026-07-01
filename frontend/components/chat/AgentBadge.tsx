import React from "react";
import type { AgentName } from "@/types";
import { AGENT_LABELS, AGENT_COLORS } from "@/types";

interface AgentBadgeProps {
  agent: string;
}

export function AgentBadge({ agent }: AgentBadgeProps) {
  const colorClass =
    AGENT_COLORS[agent as AgentName] ?? "bg-slate-100 text-slate-700";
  const label = AGENT_LABELS[agent as AgentName] ?? agent;

  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}
      aria-label={`Handled by ${label} agent`}
    >
      {label}
    </span>
  );
}
