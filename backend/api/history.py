"""
Conversation History API — /history/*
Retrieve, summarize, and delete conversation turns by session ID.
"""
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.api.auth import get_current_user
from backend.database.conversation import get_history
from backend.database.mongo import get_db

logger = logging.getLogger("techmart.history")
router = APIRouter()


@router.get("/{session_id}")
async def get_conversation_history(
    session_id: str,
    last_n: int = 50,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = str(user["_id"])

    session = await db.sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != user_id and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    turns = await get_history(session_id, last_n=last_n)

    # Return summary if already generated
    conv = await db.conversations.find_one({"session_id": session_id})
    summary = conv.get("summary") if conv else None

    return {
        "session_id": session_id,
        "title": session.get("title", "Untitled"),
        "turns": turns,
        "total_turns": len(turns),
        "summary": summary,
    }


@router.post("/{session_id}/summarize")
async def summarize_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """EN-07: Trigger AI summary generation for a session."""
    db = get_db()
    user_id = str(user["_id"])

    session = await db.sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != user_id and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    turns = await get_history(session_id, last_n=100)

    async def _generate():
        from backend.agents.summarizer import generate_summary, save_summary
        summary = await generate_summary(session_id, turns)
        await save_summary(session_id, summary)
        logger.info(f"Background summary complete for {session_id}")

    background_tasks.add_task(_generate)
    return {"message": f"Summary generation started for session {session_id}"}


@router.delete("/{session_id}")
async def delete_session_history(
    session_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = str(user["_id"])

    session = await db.sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != user_id and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # EN-07: Auto-generate summary before deletion
    turns = await get_history(session_id, last_n=100)
    if turns:
        async def _auto_summarize():
            from backend.agents.summarizer import generate_summary, save_summary
            summary = await generate_summary(session_id, turns)
            await save_summary(session_id, summary)
        background_tasks.add_task(_auto_summarize)

    await db.conversations.delete_one({"session_id": session_id})
    await db.sessions.delete_one({"session_id": session_id})
    await db.analytics.delete_one({"session_id": session_id})

    logger.info(f"Session {session_id} deleted by user {user_id}")
    return {"message": f"Session {session_id} deleted"}
