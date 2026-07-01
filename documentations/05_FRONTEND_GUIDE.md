# 05 — Frontend Architecture Guide

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Framework:** Next.js 14 (App Router) + TypeScript + Tailwind CSS

---

## Directory Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout, font, global providers
│   ├── page.tsx                # Redirect → /login or /chat
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx        # Login form
│   │   └── register/
│   │       └── page.tsx        # Register form
│   ├── chat/
│   │   └── page.tsx            # Main chat interface
│   ├── history/
│   │   └── page.tsx            # Conversation history
│   ├── analytics/
│   │   └── page.tsx            # Analytics dashboard
│   └── admin/
│       └── page.tsx            # Admin panel (KB upload)
├── components/
│   ├── chat/
│   │   ├── ChatWindow.tsx      # Message thread
│   │   ├── MessageBubble.tsx   # Single message UI
│   │   ├── MessageInput.tsx    # Input bar + send button
│   │   ├── TypingIndicator.tsx # Animated dots
│   │   └── AgentBadge.tsx      # Shows which agent responded
│   ├── layout/
│   │   ├── Sidebar.tsx         # Session list sidebar
│   │   ├── Header.tsx          # App header with user menu
│   │   └── ProtectedRoute.tsx  # Auth guard wrapper
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── RegisterForm.tsx
│   ├── analytics/
│   │   ├── ConversationChart.tsx
│   │   ├── AgentUsageChart.tsx
│   │   ├── ResponseTimeChart.tsx
│   │   └── SatisfactionChart.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Modal.tsx
│       └── Spinner.tsx
├── hooks/
│   ├── useAuth.ts              # Auth state + token management
│   ├── useChat.ts              # Send message, stream response
│   ├── useSessions.ts          # Fetch session list
│   └── useAnalytics.ts         # Fetch dashboard metrics
├── services/
│   └── api.ts                  # Axios instance with JWT interceptor
├── styles/
│   └── globals.css             # Tailwind base styles
├── types/
│   └── index.ts                # Shared TypeScript types
├── next.config.ts
├── tailwind.config.ts
└── package.json
```

---

## Initialize Next.js Project

```bash
cd frontend
npx create-next-app@latest . \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*"
```

---

## Install Additional Dependencies

```bash
npm install axios react-markdown lucide-react
npm install recharts           # analytics charts
npm install react-hot-toast    # notifications
npm install @types/node --save-dev
```

---

## services/api.ts — Axios Configuration

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 30000,
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 — redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## hooks/useAuth.ts

```typescript
import { useState, useEffect, createContext, useContext } from "react";
import api from "@/services/api";

interface AuthState {
  user: { id: string; name: string; email: string } | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
};
```

---

## hooks/useChat.ts

```typescript
import { useState } from "react";
import api from "@/services/api";

export interface Message {
  role: "user" | "assistant";
  content: string;
  agents_used?: string[];
  timestamp: string;
}

export const useChat = (sessionId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (text: string) => {
    const userMsg: Message = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const { data } = await api.post("/chat", {
        session_id: sessionId,
        message: text,
      });
      const assistantMsg: Message = {
        role: "assistant",
        content: data.response,
        agents_used: data.agents_used,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading };
};
```

---

## types/index.ts

```typescript
export interface User {
  id: string;
  name: string;
  email: string;
  role: "user" | "admin";
}

export interface Session {
  session_id: string;
  last_message: string;
  timestamp: string;
}

export interface AnalyticsSummary {
  total_conversations: number;
  avg_response_time: number;
  satisfaction_score: number;
}
```

---

## Environment Variables (frontend)

Create `frontend/.env.local`:

```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production (set in Vercel dashboard):

```ini
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## Page Routes Summary

| Route | Page | Auth Required |
|-------|------|--------------|
| `/login` | Login form | No |
| `/register` | Registration form | No |
| `/chat` | Main chat interface | Yes |
| `/history` | Past conversations | Yes |
| `/analytics` | Metrics dashboard | Yes |
| `/admin` | Knowledge base admin | Yes + Admin role |
