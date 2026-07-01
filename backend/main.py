from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database.mongo import connect_db, close_db, get_db
from backend.api import auth, chat, history, analytics, admin

app = FastAPI(
    title="Multi-Agent Customer Support API",
    version="1.0.0",
    description="AI-powered customer support with RAG and multi-agent routing",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await connect_db()
    # Ensure MongoDB indexes exist
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


@app.on_event("shutdown")
async def shutdown():
    await close_db()


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(chat.router,      prefix="/chat",      tags=["Chat"])
app.include_router(history.router,   prefix="/history",   tags=["History"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin.router,     prefix="/admin",     tags=["Admin"])
