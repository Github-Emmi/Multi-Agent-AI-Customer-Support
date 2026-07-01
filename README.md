# Multi-Agent AI Customer Support Assistant

> Enterprise-grade customer support system powered by specialized AI agents, Retrieval-Augmented Generation (RAG), and LLMs.

---

## Overview

This system routes customer queries to specialized AI agents — Billing, Technical Support, Product, Complaint, and FAQ — each grounded by a RAG pipeline over TechMart Electronics' knowledge base.

**Tech Stack:** Next.js · FastAPI · LangGraph · FAISS · sentence-transformers · MongoDB Atlas · openrouter.ai

---

## Quick Start

### 1. Clone and set up environment

```bash
git clone https://github.com/Github-Emmi/Multi-Agent-AI-Customer-Support.git
cd "Multi-Agent AI Customer Support Assistant"

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in OPENROUTER_API_KEY, MONGODB_URI, JWT_SECRET
```

### 2. Build the knowledge base index

Add PDF files to `knowledge_base/` then run:

```bash
python -m backend.rag.pipeline
```

### 3. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

---

## Project Structure

```
├── backend/           FastAPI app, agents, RAG, database
├── frontend/          Next.js chat interface
├── knowledge_base/    Company PDF documents
├── vectorstore/       FAISS index (generated)
├── datasets/          Public training/evaluation datasets
├── documentations/    Full architecture and implementation docs
└── requirements.txt
```

---

## Documentation

| File | Contents |
|------|---------|
| [00_PROJECT_ANALYSIS.md](documentations/00_PROJECT_ANALYSIS.md) | Requirements, risks, success criteria |
| [01_SYSTEM_ARCHITECTURE.md](documentations/01_SYSTEM_ARCHITECTURE.md) | Full system design and data flows |
| [02_IMPLEMENTATION_ROADMAP.md](documentations/02_IMPLEMENTATION_ROADMAP.md) | Phase-by-phase implementation plan |
| [03_ENVIRONMENT_SETUP.md](documentations/03_ENVIRONMENT_SETUP.md) | Local development setup |
| [04_BACKEND_GUIDE.md](documentations/04_BACKEND_GUIDE.md) | FastAPI architecture and API reference |
| [05_FRONTEND_GUIDE.md](documentations/05_FRONTEND_GUIDE.md) | Next.js component and hook guide |
| [06_AGENTS_GUIDE.md](documentations/06_AGENTS_GUIDE.md) | LangGraph agent system design |
| [07_RAG_PIPELINE_GUIDE.md](documentations/07_RAG_PIPELINE_GUIDE.md) | RAG ingestion and retrieval |
| [08_DATABASE_SCHEMA.md](documentations/08_DATABASE_SCHEMA.md) | MongoDB collections and schemas |
| [09_DATASETS_GUIDE.md](documentations/09_DATASETS_GUIDE.md) | Public datasets download and usage |
| [10_KNOWLEDGE_BASE_GUIDE.md](documentations/10_KNOWLEDGE_BASE_GUIDE.md) | Creating TechMart knowledge base PDFs |
| [11_DEPLOYMENT_GUIDE.md](documentations/11_DEPLOYMENT_GUIDE.md) | Vercel + Railway + MongoDB Atlas |

---

## Evaluation Criteria

| Component | Marks |
|-----------|-------|
| Frontend Design | 10 |
| Backend APIs | 15 |
| Multi-Agent Architecture | 20 |
| RAG Implementation | 20 |
| LLM Integration | 15 |
| Database Design | 10 |
| Documentation & Deployment | 10 |
| **Total** | **100** |

---

## License

MIT
