"""
Conversation History API — /history/*
Retrieve and delete conversation turns by session ID.
"""
from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import get_current_user
from backend.database.conversation import get_history
from backend.database.mongo import get_db

router = APIRouter()


@router.get("/{session_id}")
async def get_conversation_history(
    session_id: str,
    last_n: int = 50,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = str(user["_id"])

    # Verify session belongs to user
    session = await db.sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != user_id and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    turns = await get_history(session_id, last_n=last_n)
    return {
        "session_id": session_id,
        "title": session.get("title", "Untitled"),
        "turns": turns,
        "total_turns": len(turns),
    }


@router.delete("/{session_id}")
async def delete_session_history(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = str(user["_id"])

    session = await db.sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != user_id and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    await db.conversations.delete_one({"session_id": session_id})
    await db.sessions.delete_one({"session_id": session_id})
    await db.analytics.delete_one({"session_id": session_id})

    return {"message": f"Session {session_id} deleted"}
