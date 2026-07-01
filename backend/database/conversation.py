from datetime import datetime
from typing import List, Optional
from backend.database.mongo import get_db


async def create_session(user_id: str, session_id: str, first_message: str):
    db = get_db()
    await db.sessions.insert_one({
        "session_id": session_id,
        "user_id": user_id,
        "title": first_message[:60],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_resolved": False,
        "ticket_id": None,
    })


async def append_turn(
    session_id: str,
    role: str,
    content: str,
    agents_used: Optional[List[str]] = None,
    response_time_ms: Optional[int] = None,
):
    db = get_db()
    turn = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if agents_used:
        turn["agents_used"] = agents_used
    if response_time_ms is not None:
        turn["response_time_ms"] = response_time_ms

    await db.conversations.update_one(
        {"session_id": session_id},
        {"$push": {"turns": turn}},
        upsert=True,
    )
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$set": {"updated_at": datetime.utcnow()}},
    )


async def get_history(session_id: str, last_n: int = 10) -> List[dict]:
    db = get_db()
    doc = await db.conversations.find_one({"session_id": session_id})
    if not doc:
        return []
    return doc["turns"][-last_n:]


async def get_user_sessions(user_id: str, limit: int = 20) -> List[dict]:
    db = get_db()
    cursor = db.sessions.find(
        {"user_id": user_id}
    ).sort("updated_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
