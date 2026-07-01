# 01 — System Architecture

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Layer:** Full-Stack Architecture Reference

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│                                                                 │
│   Browser / Mobile  ──►  Next.js App (Vercel)                  │
│   - Chat UI                                                     │
│   - Auth Pages                                                  │
│   - Analytics Dashboard                                         │
│   - Admin Knowledge Base Panel                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │  HTTPS / REST / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API GATEWAY LAYER                         │
│                                                                 │
│   FastAPI Backend (Railway / Render)                            │
│   - /auth  — JWT authentication                                 │
│   - /chat  — Message ingestion                                  │
│   - /history — Conversation retrieval                           │
│   - /analytics — Dashboard data                                 │
│   - /admin — Knowledge base management                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────────┐
│ INTENT DETECTION│ │CONVERSATION  │ │   SESSION MANAGER    │
│    AGENT        │ │   MEMORY     │ │                      │
│                 │ │              │ │  MongoDB Atlas       │
│ LangGraph Node  │ │ MongoDB Atlas│ │  JWT + Session Store │
│ classify query  │ │ store turns  │ │                      │
└────────┬────────┘ └──────────────┘ └──────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT ROUTER                             │
│                                                                 │
│  LangGraph Orchestrator                                         │
│  Input: intent classification + query                           │
│  Output: route to one or multiple specialized agents            │
└────┬────────┬────────────┬────────────┬────────────┬───────────┘
     ▼        ▼            ▼            ▼            ▼
┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐
│ BILLING │ │TECHNICAL │ │ PRODUCT │ │COMPLAINT │ │   FAQ   │
│  AGENT  │ │ SUPPORT  │ │  AGENT  │ │  AGENT   │ │  AGENT  │
│         │ │  AGENT   │ │         │ │          │ │         │
│payments │ │login/pwd │ │features │ │escalation│ │policies │
│invoices │ │install   │ │pricing  │ │resolution│ │general  │
│refunds  │ │bugs/error│ │warranty │ │feedback  │ │contact  │
└────┬────┘ └────┬─────┘ └────┬────┘ └────┬─────┘ └────┬────┘
     └──────────┴─────────────┴────────────┴────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RAG PIPELINE LAYER                         │
│                                                                 │
│  1. Semantic Retrieval ← FAISS / Pinecone vector search         │
│  2. Context Assembly  ← top-k chunks concatenated              │
│  3. Prompt Builder    ← system prompt + context + query         │
│  4. LLM Call          ← openrouter.ai (Llama 3 / GPT / Gemini) │
│  5. Response          ← grounded, cited answer                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌──────────────────────┐      ┌─────────────────────────────┐
│   VECTOR DATABASE    │      │      KNOWLEDGE BASE         │
│                      │      │                             │
│  FAISS (local dev)   │      │  faq.pdf                    │
│  Pinecone (prod)     │      │  refund_policy.pdf          │
│                      │      │  shipping_policy.pdf        │
│  Stores:             │      │  warranty.pdf               │
│  - embeddings        │      │  user_manual.pdf            │
│  - chunk metadata    │      │  pricing.pdf                │
│  - source doc refs   │      │  products.pdf               │
└──────────────────────┘      │  installation_guide.pdf     │
                              └─────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RESPONSE AGGREGATOR                           │
│                                                                 │
│  - Merge responses from multiple agents (if multi-routed)       │
│  - Rank and deduplicate                                         │
│  - Format final response                                        │
│  - Persist to Conversation Memory                               │
│  - Return to Frontend                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Lifecycle — Detailed Flow

```
User types: "I paid yesterday but Premium is still locked."
     │
     ▼
[1] Frontend (Next.js)
     │  POST /chat { session_id, message }
     ▼
[2] FastAPI /chat endpoint
     │  validate JWT, extract session_id
     ▼
[3] Intent Detection Agent
     │  LLM classify → ["billing", "technical"]
     ▼
[4] Agent Router
     │  dispatch to Billing Agent + Technical Agent (parallel)
     ▼
[5a] Billing Agent                    [5b] Technical Agent
     │  RAG retrieve billing docs          │  RAG retrieve tech docs
     │  Build prompt + context             │  Build prompt + context
     │  LLM call → billing answer          │  LLM call → tech answer
     ▼                                     ▼
[6] Response Aggregator
     │  merge both answers
     │  compose unified response
     ▼
[7] Conversation Memory
     │  persist: user_msg, ai_response, timestamp, session_id
     ▼
[8] Return JSON response to Frontend
     ▼
[9] Frontend renders streamed response
```

---

## Component Responsibilities

### Frontend (Next.js)

| Component | Responsibility |
|-----------|---------------|
| `AuthPage` | Login / Register form, JWT token storage |
| `ChatWindow` | Real-time message display, streaming |
| `MessageInput` | Send message, typing indicator |
| `ConversationSidebar` | Session history list |
| `AnalyticsDashboard` | Charts: usage, response times, satisfaction |
| `AdminPanel` | Upload/manage knowledge base PDFs |
| `useChat` hook | WebSocket/polling, message state |
| `useAuth` hook | Token management, auth state |
| `api.service.ts` | Axios interceptors, base URL config |

### Backend (FastAPI)

| Module | Responsibility |
|--------|---------------|
| `main.py` | App init, CORS, router registration |
| `api/auth.py` | Register, login, JWT issue/verify |
| `api/chat.py` | Receive query, trigger orchestrator |
| `api/history.py` | Retrieve conversation by session |
| `api/analytics.py` | Aggregate metrics for dashboard |
| `api/admin.py` | PDF upload, re-index knowledge base |
| `agents/router.py` | LangGraph orchestrator, intent → agents |
| `agents/billing.py` | Billing domain agent |
| `agents/technical.py` | Technical support domain agent |
| `agents/product.py` | Product information domain agent |
| `agents/complaint.py` | Complaint & escalation agent |
| `agents/faq.py` | FAQ & general queries agent |
| `rag/pipeline.py` | Document ingestion, chunking, embedding |
| `rag/retriever.py` | Semantic search over vector store |
| `embeddings/encoder.py` | Sentence transformer wrapper |
| `vectorstore/faiss_store.py` | FAISS index management |
| `vectorstore/pinecone_store.py` | Pinecone cloud vector store |
| `database/mongo.py` | MongoDB Atlas connection |
| `database/conversation.py` | Conversation CRUD |
| `models/schemas.py` | Pydantic models for API validation |

---

## Data Flow — RAG Ingestion Pipeline

```
knowledge_base/*.pdf
        │
        ▼
[PyPDF] Extract raw text
        │
        ▼
[LangChain TextSplitter]
  chunk_size=500, overlap=50
        │
        ▼
[SentenceTransformer]
  all-MiniLM-L6-v2
  → 384-dim embedding vectors
        │
        ▼
[FAISS IndexFlatL2]
  store embeddings + metadata
  (source_file, page, chunk_id)
        │
        ▼
[Persist to disk]
  vectorstore/faiss_index/
```

---

## Security Architecture

| Concern | Solution |
|---------|---------|
| Authentication | JWT (HS256), expiry 24h, refresh tokens |
| Authorization | Role-based: user / admin |
| Input validation | Pydantic schemas on all API inputs |
| PDF upload security | MIME type + size validation, virus scan |
| CORS | Allowlist frontend domain only |
| Secrets | Environment variables, never in code |
| Database | MongoDB Atlas IP allowlist + auth |
| HTTPS | Enforced on Vercel + Railway/Render |

---

## Scalability Design

```
Load Balancer
     │
┌────┴─────┐
│ FastAPI  │ ← multiple instances (Railway auto-scale)
│ Instance │
└────┬─────┘
     │
┌────┴────────────────┐
│  LangGraph          │  ← stateless, scale horizontally
│  Agent Workers      │
└────┬────────────────┘
     │
┌────┴────────┐    ┌────────────────┐
│  FAISS      │    │  MongoDB Atlas │
│  (per pod)  │    │  (shared)      │
└─────────────┘    └────────────────┘
```

> **Production note:** Migrate FAISS to Pinecone for shared vector state across multiple backend instances.
