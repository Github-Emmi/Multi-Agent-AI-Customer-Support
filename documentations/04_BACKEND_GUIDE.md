# 04 — Backend Architecture Guide

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Framework:** Python FastAPI + LangGraph  
> **Database:** MongoDB Atlas

---

## Directory Structure

```
backend/
├── main.py                    # App entry point
├── config.py                  # Settings from .env
├── api/
│   ├── __init__.py
│   ├── auth.py                # /auth/* endpoints
│   ├── chat.py                # /chat endpoint
│   ├── history.py             # /history endpoint
│   ├── analytics.py           # /analytics endpoint
│   └── admin.py               # /admin/* endpoints
├── agents/
│   ├── __init__.py
│   ├── router.py              # LangGraph orchestrator
│   ├── billing.py             # Billing domain agent
│   ├── technical.py           # Technical support agent
│   ├── product.py             # Product info agent
│   ├── complaint.py           # Complaint/escalation agent
│   └── faq.py                 # FAQ agent
├── rag/
│   ├── __init__.py
│   ├── pipeline.py            # Ingestion: PDF → chunks → embeddings
│   └── retriever.py           # Semantic search
├── embeddings/
│   ├── __init__.py
│   └── encoder.py             # SentenceTransformer wrapper
├── vectorstore/
│   ├── __init__.py
│   ├── faiss_store.py         # FAISS local index
│   └── pinecone_store.py      # Pinecone cloud index
├── database/
│   ├── __init__.py
│   ├── mongo.py               # MongoDB connection
│   └── conversation.py        # Conversation CRUD operations
└── models/
    ├── __init__.py
    └── schemas.py             # Pydantic request/response models
```

---

## main.py — Application Bootstrap

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import auth, chat, history, analytics, admin
from backend.config import settings

app = FastAPI(title="Multi-Agent Customer Support API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(history.router, prefix="/history", tags=["History"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

---

## API Endpoints — Complete Reference

### Authentication (`/auth`)

| Method | Path | Auth | Request Body | Response |
|--------|------|------|-------------|---------|
| POST | `/auth/register` | No | `{name, email, password}` | `{user_id, token}` |
| POST | `/auth/login` | No | `{email, password}` | `{token, user}` |
| POST | `/auth/logout` | JWT | — | `{message}` |
| POST | `/auth/reset-password` | No | `{email}` | `{message}` |
| PUT | `/auth/reset-password/confirm` | No | `{token, new_password}` | `{message}` |
| GET | `/auth/me` | JWT | — | `{user}` |

### Chat (`/chat`)

| Method | Path | Auth | Request Body | Response |
|--------|------|------|-------------|---------|
| POST | `/chat` | JWT | `{session_id, message}` | `{response, agents_used, session_id}` |
| GET | `/chat/sessions` | JWT | — | `[{session_id, last_message, timestamp}]` |

### History (`/history`)

| Method | Path | Auth | Response |
|--------|------|------|---------|
| GET | `/history/{session_id}` | JWT | `[{role, content, timestamp}]` |
| DELETE | `/history/{session_id}` | JWT | `{message}` |

### Analytics (`/analytics`)

| Method | Path | Auth | Response |
|--------|------|------|---------|
| GET | `/analytics/summary` | JWT | `{total_conversations, avg_response_time, satisfaction_score}` |
| GET | `/analytics/agent-usage` | JWT | `[{agent, count}]` |
| GET | `/analytics/daily` | JWT | `[{date, count}]` |
| POST | `/analytics/feedback` | JWT | `{session_id, rating, comment}` |

### Admin (`/admin`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| POST | `/admin/upload` | JWT+Admin | Upload PDF to knowledge base |
| POST | `/admin/reindex` | JWT+Admin | Re-run ingestion pipeline |
| GET | `/admin/documents` | JWT+Admin | List ingested documents |
| DELETE | `/admin/documents/{id}` | JWT+Admin | Remove document and re-index |

---

## config.py — Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    MONGODB_URI: str
    JWT_SECRET: str
    JWT_EXPIRY_HOURS: int = 24
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "techmart-kb"
    SMTP_HOST: str = ""
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## models/schemas.py — Pydantic Models

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Auth
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str  # min 8 chars enforced in validator

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str
    user_id: str
    name: str

# Chat
class ChatRequest(BaseModel):
    session_id: str
    message: str   # max 2000 chars enforced in validator

class ChatResponse(BaseModel):
    response: str
    agents_used: List[str]
    session_id: str
    response_time_ms: int

# Conversation Turn
class ConversationTurn(BaseModel):
    role: str           # "user" | "assistant"
    content: str
    timestamp: datetime
    agents_used: Optional[List[str]] = None

# Analytics Feedback
class FeedbackRequest(BaseModel):
    session_id: str
    rating: int         # 1-5
    comment: Optional[str] = None
```

---

## database/mongo.py — Connection

```python
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

client: AsyncIOMotorClient = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client.customer_support

async def close_db():
    if client:
        client.close()
```

---

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all backend tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```
