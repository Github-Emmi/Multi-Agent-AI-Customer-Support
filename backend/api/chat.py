"""
Chat API — /chat/*
Receives user messages, routes through LangGraph orchestrator,
persists conversation, returns agent response.
"""
import time
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from backend.api.auth import get_current_user
from backend.agents.router import run_agents
from backend.database.conversation import (
    create_session,
    append_turn,
    get_history,
    get_user_sessions,
)
from backend.database.mongo import get_db
from backend.models.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = str(user["_id"])
    session_id = body.session_id

    # Create session if new
    existing_session = await db.sessions.find_one({"session_id": session_id})
    if not existing_session:
        await create_session(user_id, session_id, body.message)

    # Load last 10 turns for context
    history = await get_history(session_id, last_n=10)

    # Persist user message
    await append_turn(session_id, "user", body.message)

    # Run LangGraph agent pipeline
    start_ms = int(time.time() * 1000)
    result = await run_agents(
        query=body.message,
        session_id=session_id,
        conversation_history=history,
    )
    response_time_ms = int(time.time() * 1000) - start_ms

    final_response = result.get("final_response", "I was unable to process your request.")
    agents_used = result.get("agents_used", [])

    # Persist assistant response
    await append_turn(
        session_id=session_id,
        role="assistant",
        content=final_response,
        agents_used=agents_used,
        response_time_ms=response_time_ms,
    )

    # Store analytics record
    await db.analytics.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "user_id": user_id,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
            },
            "$push": {
                "agents_used_history": {"$each": agents_used},
                "response_times": response_time_ms,
            },
            "$inc": {"total_turns": 1},
        },
        upsert=True,
    )

    return ChatResponse(
        response=final_response,
        agents_used=agents_used,
        session_id=session_id,
        response_time_ms=response_time_ms,
    )


@router.get("/sessions")
async def get_sessions(user: dict = Depends(get_current_user)):
    user_id = str(user["_id"])
    sessions = await get_user_sessions(user_id, limit=20)
    return [
        {
            "session_id": s["session_id"],
            "title": s.get("title", "Untitled"),
            "last_message": s.get("updated_at"),
            "is_resolved": s.get("is_resolved", False),
        }
        for s in sessions
    ]


@router.post("/new-session")
async def new_session(user: dict = Depends(get_current_user)):
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    return {"session_id": session_id}
