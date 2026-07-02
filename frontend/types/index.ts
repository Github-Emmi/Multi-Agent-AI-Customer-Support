// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  user_id: string;
  name: string;
  email: string;
  role: "user" | "admin";
  created_at?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  token: string;
  user_id: string;
  name: string;
  role: string;
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export interface Message {
  role: MessageRole;
  content: string;
  timestamp: string;
  agents_used?: string[];
  response_time_ms?: number;
}

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface ChatResponse {
  response: string;
  agents_used: string[];
  session_id: string;
  response_time_ms: number;
}

// ── Session ───────────────────────────────────────────────────────────────────

export interface Session {
  session_id: string;
  title: string;
  last_message?: string;
  is_resolved: boolean;
}

export interface ConversationHistory {
  session_id: string;
  title: string;
  turns: Message[];
  total_turns: number;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface AnalyticsSummary {
  total_conversations: number;
  avg_response_time_ms: number;
  satisfaction_score: number;
}

export interface AgentUsageItem {
  agent: string;
  count: number;
}

export interface DailyConversation {
  date: string;
  count: number;
}

export interface FeedbackPayload {
  session_id: string;
  rating: number;
  comment?: string;
}

// ── Admin ─────────────────────────────────────────────────────────────────────

export interface KBDocument {
  filename: string;
  file_size_bytes: number;
  is_indexed: boolean;
  uploaded_at: string;
  last_indexed_at?: string;
}

// ── Tickets ───────────────────────────────────────────────────────────────────

export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
export type TicketPriority = "low" | "medium" | "high" | "urgent";

export interface Ticket {
  ticket_id: string;
  session_id: string;
  user_id: string;
  subject: string;
  description?: string;
  status: TicketStatus;
  priority: TicketPriority;
  handoff?: boolean;
  assigned_agent?: string | null;
  created_at: string;
  updated_at?: string;
  resolved_at?: string | null;
}

export interface CreateTicketPayload {
  session_id: string;
  subject: string;
  description?: string;
  priority?: TicketPriority;
}

export interface HandoffPayload {
  session_id: string;
  reason?: string;
}

// ── Voice ─────────────────────────────────────────────────────────────────────

export interface VoiceResponse {
  transcription: string;
  response: string;
  agents_used: string[];
  session_id: string;
  response_time_ms: number;
}

// ── Conversation Summary ──────────────────────────────────────────────────────

export interface ConversationSummary {
  session_id: string;
  summary_text: string;
  issue?: string;
  agents?: string[];
  resolution?: string;
  sentiment?: string;
  action_required?: boolean;
}

// ── Extended Analytics ────────────────────────────────────────────────────────

export interface SatisfactionDistribution {
  distribution: Record<string, number>;
}

export interface SentimentTrend {
  date: string;
  avg_sentiment: number;
  count: number;
}

export interface TicketStats {
  total: number;
  by_status: Record<string, number>;
}

// ── Agent ─────────────────────────────────────────────────────────────────────

export type AgentName = "billing" | "technical" | "product" | "complaint" | "faq";

export const AGENT_LABELS: Record<AgentName, string> = {
  billing: "Billing",
  technical: "Technical Support",
  product: "Product",
  complaint: "Complaint",
  faq: "FAQ",
};

export const AGENT_COLORS: Record<AgentName, string> = {
  billing: "bg-emerald-100 text-emerald-800",
  technical: "bg-blue-100 text-blue-800",
  product: "bg-violet-100 text-violet-800",
  complaint: "bg-rose-100 text-rose-800",
  faq: "bg-amber-100 text-amber-800",
};
