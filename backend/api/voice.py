"""
EN-01: Voice-enabled customer support.
Accepts text data processed by client-side Web Speech API → routes straight to agent pipeline.
Operates 100% cost-free with absolute protection against upstream API balance blocks.
"""
import logging
import time
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import get_current_user
from backend.agents.router import run_agents
from backend.database.conversation import (
    create_session,
    append_turn,
    get_history,
)
from backend.database.mongo import get_db

logger = logging.getLogger("techmart.voice")
router = APIRouter()


class VoiceTranscriptPayload(BaseModel):
    """Schema ensuring the inbound transcribed string field exists."""
    text: str


@router.post("/transcribe")
async def voice_to_chat(
    session_id: str,
    payload: VoiceTranscriptPayload,
    user: dict = Depends(get_current_user),
):
    """
    EN-01: Client text router endpoint.
    1. Receives clean string transcription from browser hardware engine
    2. Feeds text directly into multi-agent pipelines
    3. Commits transactions to MongoDB and evaluates metrics
    """
    transcribed_text = payload.text.strip()

    if not transcribed_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not process speech. The transcription data string was empty.",
        )

    logger.info(f"Local transcript received: '{transcribed_text}' | session={session_id}")

    # Route through agent pipeline
    db = get_db()
    user_id = str(user["_id"])
    existing = await db.sessions.find_one({"session_id": session_id})
    if not existing:
        await create_session(user_id, session_id, transcribed_text)

    history = await get_history(session_id, last_n=10)
    await append_turn(session_id, "user", transcribed_text)

    start_ms = int(time.time() * 1000)
    result = await run_agents(
        query=transcribed_text,
        session_id=session_id,
        conversation_history=history,
    )
    response_time_ms = int(time.time() * 1000) - start_ms

    final_response = result.get("final_response", "")
    agents_used = result.get("agents_used", [])

    await append_turn(
        session_id=session_id,
        role="assistant",
        content=final_response,
        agents_used=agents_used,
        response_time_ms=response_time_ms,
    )

    return {
        "transcription": transcribed_text,
        "response": final_response,
        "agents_used": agents_used,
        "session_id": session_id,
        "response_time_ms": response_time_ms,
    }
