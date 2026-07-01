# 02 — Step-by-Step Implementation Roadmap

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Methodology:** Phased delivery — foundation → agents → RAG → frontend → enhancements → deployment

---

## Overview

| Phase | Name | Key Deliverable |
|-------|------|----------------|
| 0 | Environment Setup | All tools installed, project initialized |
| 1 | Planning & Design | Architecture confirmed, wireframes, Git repo |
| 2 | Backend Foundation | FastAPI running, auth, MongoDB, session |
| 3 | AI Agents | Intent detection, router, 5 specialized agents |
| 4 | RAG Pipeline | Documents ingested, embeddings stored, retrieval working |
| 5 | LLM Integration | Agents generating grounded responses via openrouter.ai |
| 6 | Frontend | Next.js chat UI, auth pages, conversation history |
| 7 | Analytics Dashboard | Real-time metrics, satisfaction tracking |
| 8 | Enhancements | Sentiment routing, summaries, ticket creation, admin panel |
| 9 | Testing | Unit, integration, E2E tests passing |
| 10 | Deployment | Live on Vercel + Railway/Render + MongoDB Atlas |

---

## Phase 0 — Environment Setup

### Prerequisites

- [ ] macOS / Linux / WSL2 with zsh or bash
- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Node.js 20+ installed (`node --version`)
- [ ] Git installed and configured
- [ ] Docker Desktop installed
- [ ] VS Code with Python and ESLint extensions
- [ ] GitHub account and `gh` CLI authenticated

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Github-Emmi/Multi-Agent-AI-Customer-Support.git
cd "Multi-Agent AI Customer Support Assistant"

# 2. Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Node.js dependencies (after frontend scaffolding)
cd frontend && npm install && cd ..

# 5. Copy environment variables template
cp .env.example .env
# Fill in: OPENROUTER_API_KEY, MONGODB_URI, JWT_SECRET, PINECONE_API_KEY
```

### Required API Keys / Accounts

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [openrouter.ai](https://openrouter.ai) | LLM API gateway | Yes |
| [MongoDB Atlas](https://cloud.mongodb.com) | Database | 512 MB free |
| [Pinecone](https://pinecone.io) | Cloud vector DB | 1 index free |
| [Vercel](https://vercel.com) | Frontend hosting | Yes |
| [Railway](https://railway.app) | Backend hosting | $5/mo credit |

---

## Phase 1 — Planning & Design

### Steps

- [ ] **1.1** Review `Multi_Agent_Documentations.md` end-to-end
- [ ] **1.2** Review `documentations/00_PROJECT_ANALYSIS.md`
- [ ] **1.3** Review `documentations/01_SYSTEM_ARCHITECTURE.md`
- [ ] **1.4** Create UI wireframes for:
  - Login / Register page
  - Main chat window
  - Conversation history sidebar
  - Analytics dashboard
  - Admin panel (knowledge base upload)
- [ ] **1.5** Define fictional company: **TechMart Electronics**
- [ ] **1.6** Design MongoDB collections (see `06_DATABASE_SCHEMA.md`)
- [ ] **1.7** Define API contract (REST endpoints, request/response shapes)
- [ ] **1.8** Git: branch strategy — `main` (prod), `dev` (active), feature branches

### Git Branch Strategy

```
main ──────────────────────────────────────► production
  └── dev ──────────────────────────────────► staging
        ├── feature/backend-auth
        ├── feature/intent-detection
        ├── feature/rag-pipeline
        ├── feature/billing-agent
        └── feature/frontend-chat
```

---

## Phase 2 — Backend Foundation

### Steps

- [ ] **2.1** Initialize FastAPI application (`backend/main.py`)
- [ ] **2.2** Configure CORS for frontend domain
- [ ] **2.3** Set up MongoDB Atlas connection (`backend/database/mongo.py`)
- [ ] **2.4** Implement User model and auth schemas (`backend/models/schemas.py`)
- [ ] **2.5** Implement `/auth/register` endpoint — hash password with bcrypt
- [ ] **2.6** Implement `/auth/login` endpoint — issue JWT
- [ ] **2.7** Implement JWT middleware for protected routes
- [ ] **2.8** Implement password reset flow with email verification
- [ ] **2.9** Implement session management — store active sessions in MongoDB
- [ ] **2.10** Write unit tests for auth endpoints
- [ ] **2.11** Run: `uvicorn backend.main:app --reload`

### API Endpoints — Phase 2

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Create new user |
| POST | `/auth/login` | No | Login, return JWT |
| POST | `/auth/logout` | Yes | Invalidate session |
| POST | `/auth/reset-password` | No | Send reset email |
| PUT | `/auth/reset-password/confirm` | No | Set new password |
| GET | `/auth/me` | Yes | Get current user |

---

## Phase 3 — AI Agent Development

### Steps

- [ ] **3.1** Install and configure LangGraph
- [ ] **3.2** Define agent state schema (LangGraph `TypedDict`)
- [ ] **3.3** Implement Intent Detection Agent (`backend/agents/router.py`)
  - Input: user query string
  - Output: list of intent labels from `["billing", "technical", "product", "complaint", "faq"]`
  - Method: LLM zero-shot classification with structured output
- [ ] **3.4** Implement Agent Router (LangGraph conditional edges)
  - Map intents → agent nodes
  - Support multi-agent dispatch (parallel branches)
- [ ] **3.5** Implement Billing Agent (`backend/agents/billing.py`)
- [ ] **3.6** Implement Technical Support Agent (`backend/agents/technical.py`)
- [ ] **3.7** Implement Product Agent (`backend/agents/product.py`)
- [ ] **3.8** Implement Complaint Agent (`backend/agents/complaint.py`)
- [ ] **3.9** Implement FAQ Agent (`backend/agents/faq.py`)
- [ ] **3.10** Implement Response Aggregator (merge multi-agent outputs)
- [ ] **3.11** Wire `/chat` endpoint to LangGraph orchestrator
- [ ] **3.12** Test routing with sample queries for each domain

### Agent Node Template

Each agent follows this interface:

```python
def agent_node(state: AgentState) -> AgentState:
    # 1. Extract query and retrieved context from state
    # 2. Build domain-specific system prompt
    # 3. Call LLM via openrouter.ai
    # 4. Append response to state
    return state
```

---

## Phase 4 — RAG Pipeline

### Steps

- [ ] **4.1** Create TechMart Electronics knowledge base PDFs (see `09_KNOWLEDGE_BASE_GUIDE.md`)
- [ ] **4.2** Implement PDF ingestion script (`backend/rag/pipeline.py`)
  - Load PDFs with PyPDF
  - Split into chunks (500 tokens, 50 overlap)
- [ ] **4.3** Implement embedding generation (`backend/embeddings/encoder.py`)
  - Use `sentence-transformers/all-MiniLM-L6-v2`
- [ ] **4.4** Implement FAISS index creation (`backend/vectorstore/faiss_store.py`)
  - Store embeddings + metadata (source, page, chunk_id)
  - Persist index to disk
- [ ] **4.5** Implement semantic retrieval (`backend/rag/retriever.py`)
  - Query embedding → FAISS similarity search → top-k chunks
- [ ] **4.6** Run ingestion: `python backend/rag/pipeline.py`
- [ ] **4.7** Test retrieval with domain-specific questions
- [ ] **4.8** (Production) Implement Pinecone store (`backend/vectorstore/pinecone_store.py`)
- [ ] **4.9** Implement `/admin/reindex` endpoint to re-ingest after PDF updates

### Ingestion Run Command

```bash
python -m backend.rag.pipeline \
  --source knowledge_base/ \
  --output vectorstore/faiss_index/
```

---

## Phase 5 — LLM Integration

### Steps

- [ ] **5.1** Create openrouter.ai account and obtain API key
- [ ] **5.2** Implement LLM client wrapper (`backend/models/llm_client.py`)
  - Model: `meta-llama/llama-3-8b-instruct` (default)
  - Fallback: `openai/gpt-3.5-turbo`
- [ ] **5.3** Implement system prompts for each agent
  - Each prompt scopes the agent to its domain
  - Include retrieved context in `[CONTEXT]` block
- [ ] **5.4** Connect RAG retriever output into each agent's prompt
- [ ] **5.5** Implement streaming response support (SSE)
- [ ] **5.6** Add conversation history to prompts (last 5 turns)
- [ ] **5.7** Test end-to-end: query → intent → route → RAG → LLM → response

### Prompt Template Structure

```
You are the {AGENT_DOMAIN} specialist for TechMart Electronics.
Only answer questions related to {AGENT_DOMAIN}.
If the question is outside your domain, say "This will be handled by another specialist."

[RETRIEVED CONTEXT]
{context}

[CONVERSATION HISTORY]
{history}

[CUSTOMER QUERY]
{query}

[YOUR RESPONSE]
```

---

## Phase 6 — Frontend Development

### Steps

- [ ] **6.1** Initialize Next.js app: `npx create-next-app@latest frontend --typescript --tailwind --eslint --app`
- [ ] **6.2** Install dependencies: `axios`, `socket.io-client`, `react-markdown`, `lucide-react`
- [ ] **6.3** Implement `AuthContext` and `useAuth` hook
- [ ] **6.4** Build Login page (`/login`)
- [ ] **6.5** Build Register page (`/register`)
- [ ] **6.6** Build main Chat layout (`/chat`)
  - Conversation sidebar (session list)
  - Chat window (message thread)
  - Message input with send button
  - Typing indicator (streaming dots)
- [ ] **6.7** Implement `useChat` hook — POST to `/chat`, stream response
- [ ] **6.8** Build Conversation History page (`/history`)
- [ ] **6.9** Connect frontend to FastAPI backend via Axios with JWT headers
- [ ] **6.10** Handle error states (offline, API error, timeout)
- [ ] **6.11** Mobile responsive with Tailwind CSS

---

## Phase 7 — Analytics Dashboard

### Steps

- [ ] **7.1** Implement metrics aggregation in MongoDB (`backend/api/analytics.py`)
- [ ] **7.2** Track per-conversation: agent used, response time, satisfaction score
- [ ] **7.3** Build Analytics Dashboard page (`/analytics`)
  - Total conversations (daily/weekly)
  - Agent usage breakdown (bar chart)
  - Average response time (line chart)
  - Satisfaction score distribution (pie chart)
- [ ] **7.4** Implement satisfaction feedback widget (thumbs up/down + optional text)
- [ ] **7.5** Implement Admin Panel (`/admin`) for knowledge base PDF upload and re-index

---

## Phase 8 — Enhancements

- [ ] **8.1** Sentiment analysis — detect frustrated customers, elevate to Complaint Agent
- [ ] **8.2** Automatic ticket creation — generate ticket ID, persist to MongoDB
- [ ] **8.3** AI-generated conversation summaries (summarize on session end)
- [ ] **8.4** Multilingual support — detect language, respond in same language
- [ ] **8.5** Voice input — browser `SpeechRecognition` API → text → chat pipeline
- [ ] **8.6** Human-agent handoff — flag conversation for human review, notify via email
- [ ] **8.7** Email integration — nodemailer (password reset, ticket confirmation)
- [ ] **8.8** Customer satisfaction feedback analytics — dashboard charts

---

## Phase 9 — Testing & Evaluation

### Test Coverage Targets

| Layer | Type | Tool | Target |
|-------|------|------|--------|
| Backend API | Unit | pytest | 80%+ |
| Agent routing | Integration | pytest | All intent combinations |
| RAG retrieval | Evaluation | RAGAS | Precision ≥ 80% |
| Frontend | Component | Jest + RTL | 70%+ |
| E2E | End-to-End | Playwright | All critical flows |

### Critical Test Scenarios

- [ ] Register + Login + JWT refresh
- [ ] Single-intent routing (billing only)
- [ ] Multi-intent routing (billing + technical)
- [ ] RAG returns correct document chunks
- [ ] LLM response stays in domain scope
- [ ] Conversation history persists across sessions
- [ ] Analytics metrics match stored data
- [ ] Admin PDF upload triggers re-index
- [ ] Error handling: invalid JWT, empty query, PDF parse failure

---

## Phase 10 — Deployment

### Steps

- [ ] **10.1** Configure `.env.production` with production secrets
- [ ] **10.2** Build and test Docker container for backend
- [ ] **10.3** Deploy backend to Railway: `railway up`
- [ ] **10.4** Set environment variables in Railway dashboard
- [ ] **10.5** Deploy frontend to Vercel: `vercel --prod`
- [ ] **10.6** Set `NEXT_PUBLIC_API_URL` in Vercel to Railway backend URL
- [ ] **10.7** Confirm MongoDB Atlas network access allows Railway IPs
- [ ] **10.8** Run E2E Playwright tests against production URLs
- [ ] **10.9** Record demonstration video
- [ ] **10.10** Submit deliverables (see `Multi_Agent_Documentations.md` §13)

---

## Evaluation Criteria Mapping

| Component | Marks | Phases That Deliver It |
|-----------|-------|----------------------|
| Frontend Design | 10 | Phase 6, 7 |
| Backend APIs | 15 | Phase 2, 3, 5 |
| Multi-Agent Architecture | 20 | Phase 3 |
| RAG Implementation | 20 | Phase 4, 5 |
| LLM Integration | 15 | Phase 5 |
| Database Design | 10 | Phase 2 |
| Documentation & Deployment | 10 | Phase 0, 10 |
| **Total** | **100** | |
