# 03 — Environment Setup Guide

> **Project:** Multi-Agent AI Customer Support Assistant  
> **OS:** macOS (also works on Linux / WSL2)

---

## 1. System Prerequisites

```bash
# Verify Python 3.11+
python3 --version

# Verify Node.js 20+
node --version
npm --version

# Verify Git
git --version

# Verify Docker
docker --version
docker compose version
```

Install any missing tools:

```bash
# macOS — install via Homebrew
brew install python@3.11 node git
brew install --cask docker
```

---

## 2. Clone and Initialize Project

```bash
git clone https://github.com/Github-Emmi/Multi-Agent-AI-Customer-Support.git
cd "Multi-Agent AI Customer Support Assistant"

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux

# Verify activation
which python   # should point to .venv/bin/python
```

---

## 3. Python Dependencies

Install all backend dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verify key packages:

```bash
python -c "import fastapi; print('FastAPI OK')"
python -c "import langchain; print('LangChain OK')"
python -c "import faiss; print('FAISS OK')"
python -c "from sentence_transformers import SentenceTransformer; print('SentenceTransformers OK')"
```

---

## 4. Node.js / Frontend Dependencies

```bash
cd frontend
npm install
npm run dev   # verify Next.js starts on http://localhost:3000
cd ..
```

---

## 5. Environment Variables

Copy the template and fill in all values:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# LLM
OPENROUTER_API_KEY=sk-or-...

# Database
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/customer_support

# Auth
JWT_SECRET=your-super-secret-key-min-32-chars
JWT_EXPIRY_HOURS=24

# Vector Store (Production)
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=techmart-kb

# Email (Password Reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=app-specific-password

# App
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

> **Security:** Never commit `.env` to Git. It is already in `.gitignore`.

---

## 6. MongoDB Atlas Setup

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com) → Create free cluster
2. Create database user with read/write permissions
3. Add your IP address to Network Access (or `0.0.0.0/0` for dev)
4. Get connection string → paste as `MONGODB_URI` in `.env`
5. Create database named `customer_support`

---

## 7. openrouter.ai Setup

1. Go to [openrouter.ai](https://openrouter.ai) → Sign up
2. Navigate to Keys → Create API key
3. Add key as `OPENROUTER_API_KEY` in `.env`
4. Recommended free models:
   - `meta-llama/llama-3-8b-instruct:free`
   - `mistralai/mistral-7b-instruct:free`

---

## 8. Run Backend Server

```bash
# From project root with .venv activated
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Verify: open [http://localhost:8000/docs](http://localhost:8000/docs) — FastAPI Swagger UI

---

## 9. Run Frontend Dev Server

```bash
cd frontend
npm run dev
```

Verify: open [http://localhost:3000](http://localhost:3000)

---

## 10. Ingest Knowledge Base

After creating PDFs in `knowledge_base/`:

```bash
python -m backend.rag.pipeline
```

This creates the FAISS index at `vectorstore/faiss_index/`.

---

## 11. VS Code Workspace Settings

Recommended extensions (install via VS Code):

- `ms-python.python`
- `ms-python.black-formatter`
- `bradlc.vscode-tailwindcss`
- `esbenp.prettier-vscode`
- `dbaeumer.vscode-eslint`
- `mongodb.mongodb-vscode`

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## 12. Docker (Optional — Local Full Stack)

```bash
docker compose up --build
```

This starts:
- FastAPI backend on port 8000
- Next.js frontend on port 3000
- MongoDB on port 27017 (local only)
