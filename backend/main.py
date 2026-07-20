import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.config import settings
from backend.database.mongo import connect_db, close_db, get_db
from backend.api import auth, chat, history, analytics, admin, tickets, voice, webhooks

# ── Structured logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logging.getLogger("langgraph").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

logger = logging.getLogger("techmart.api")

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)

app = FastAPI(
    title="Multi-Agent Customer Support API",
    version="1.0.0",
    description="AI-powered customer support with RAG and multi-agent routing",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("Starting TechMart Customer Support API...")
    await connect_db()
    db = get_db()
    await db.users.create_index("email", unique=True)
    await db.users.create_index("reset_token", sparse=True)
    await db.sessions.create_index("session_id", unique=True)
    await db.sessions.create_index("user_id")
    await db.sessions.create_index([("updated_at", -1)])
    await db.conversations.create_index("session_id", unique=True)
    await db.analytics.create_index("date")
    await db.analytics.create_index("user_id")
    await db.tickets.create_index("ticket_id", unique=True)
    await db.tickets.create_index("user_id")
    await db.tickets.create_index("status")
    logger.info("MongoDB indexes ensured. API ready.")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down API...")
    await close_db()


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT, "version": "1.0.0"}


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(chat.router,      prefix="/chat",      tags=["Chat"])
app.include_router(history.router,   prefix="/history",   tags=["History"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin.router,     prefix="/admin",     tags=["Admin"])
app.include_router(tickets.router,   prefix="/tickets",   tags=["Tickets"])
app.include_router(voice.router,     prefix="/voice",     tags=["Voice"])
app.include_router(webhooks.router,  prefix="/webhooks",  tags=["Webhooks"])
