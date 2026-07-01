# 11 — Deployment Guide

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Frontend:** Vercel  
> **Backend:** Railway (preferred) or Render  
> **Database:** MongoDB Atlas

---

## Pre-Deployment Checklist

- [ ] All tests passing locally (`pytest` + `npm test`)
- [ ] `.env.production` configured with real API keys
- [ ] FAISS index built from production knowledge base
- [ ] MongoDB Atlas cluster provisioned (M0 free tier)
- [ ] openrouter.ai key has sufficient credits
- [ ] Docker image builds cleanly

---

## 1. MongoDB Atlas (Database)

### Setup

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com)
2. Create **M0 free cluster** (region: us-east-1 recommended)
3. Database Access → Add User: `admin_user` with `readWriteAnyDatabase`
4. Network Access → Add IP: `0.0.0.0/0` *(restrict to Railway IPs in production)*
5. Get connection string:
   ```
   mongodb+srv://admin_user:<password>@cluster0.xxxxx.mongodb.net/customer_support
   ```
6. Create database: `customer_support` (auto-created on first write)

---

## 2. Backend — Railway Deployment

### Prepare Backend

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY vectorstore/ ./vectorstore/
COPY .env.production .env

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port 8000",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Deploy

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project (run from workspace root)
railway init

# Set environment variables
railway variables set OPENROUTER_API_KEY=sk-or-...
railway variables set MONGODB_URI=mongodb+srv://...
railway variables set JWT_SECRET=...
railway variables set FRONTEND_URL=https://your-app.vercel.app
railway variables set ENVIRONMENT=production

# Deploy
railway up

# Get deployed URL
railway domain
```

### Verify Backend

```bash
curl https://your-backend.railway.app/health
# Expected: {"status": "ok"}

curl https://your-backend.railway.app/docs
# FastAPI Swagger UI
```

---

## 3. Frontend — Vercel Deployment

### Prepare Frontend

Create `frontend/vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.railway.app/:path*"
    }
  ]
}
```

### Deploy

```bash
# Install Vercel CLI
npm install -g vercel

cd frontend

# Login and deploy
vercel login
vercel --prod

# Set environment variable in Vercel dashboard:
# NEXT_PUBLIC_API_URL = https://your-backend.railway.app
```

### Or via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import from GitHub: `Github-Emmi/Multi-Agent-AI-Customer-Support`
3. Set **Root Directory** to `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL` = Railway backend URL
5. Deploy

---

## 4. Docker Compose (Local Full Stack)

Create `docker-compose.yml`:

```yaml
version: "3.9"

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017/customer_support
      - JWT_SECRET=${JWT_SECRET}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - FRONTEND_URL=http://localhost:3000
      - ENVIRONMENT=development
    volumes:
      - ./vectorstore:/app/vectorstore
      - ./knowledge_base:/app/knowledge_base
    depends_on:
      - mongo

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

```bash
docker compose up --build
```

---

## 5. FAISS Index in Production

The FAISS index must be included in the Docker image OR mounted as a volume.

**Option A — Bake index into image (simple):**
Run `python -m backend.rag.pipeline` locally before `docker build`, so `vectorstore/faiss_index/` is committed.

**Option B — Volume mount (recommended):**
Mount `vectorstore/` as a Railway persistent volume:
```bash
railway volume create vectorstore --mount /app/vectorstore
```

**Option C — Migrate to Pinecone:**
For true stateless scalability, use Pinecone. Set `VECTOR_STORE=pinecone` in env and use `backend/vectorstore/pinecone_store.py`.

---

## 6. Environment Variables — Production

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | openrouter.ai API key |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `JWT_SECRET` | Random 32+ char string (never share) |
| `JWT_EXPIRY_HOURS` | 24 |
| `PINECONE_API_KEY` | (If using Pinecone) |
| `PINECONE_INDEX_NAME` | `techmart-kb` |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_USER` | Gmail address for password resets |
| `SMTP_PASS` | Gmail App Password |
| `FRONTEND_URL` | `https://your-app.vercel.app` |
| `ENVIRONMENT` | `production` |

---

## 7. Post-Deployment Verification

```bash
# 1. Health check
curl https://your-backend.railway.app/health

# 2. Register a user
curl -X POST https://your-backend.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}'

# 3. Login
curl -X POST https://your-backend.railway.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# 4. Send a chat message (replace TOKEN)
curl -X POST https://your-backend.railway.app/chat \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"sess_test_001","message":"What is your refund policy?"}'
```

---

## 8. Monitoring

| Tool | Purpose | Setup |
|------|---------|-------|
| Railway Logs | Backend logs, errors | `railway logs` |
| Vercel Analytics | Frontend performance | Enable in Vercel dashboard |
| MongoDB Atlas Monitoring | DB performance, slow queries | Atlas → Performance Advisor |
| UptimeRobot | Uptime alerting (free) | Monitor `/health` endpoint |
