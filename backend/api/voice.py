"""
EN-01: Voice-enabled customer support.
Accepts audio file upload → transcribes via OpenAI Whisper API → routes to chat pipeline.
Returns both the transcribed text and the agent's response.
"""
import logging
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
import httpx

from backend.api.auth import get_current_user
from backend.agents.router import run_agents
from backend.database.conversation import (
    create_session,
    append_turn,
    get_history,
)
from backend.database.mongo import get_db
from backend.config import settings

logger = logging.getLogger("techmart.voice")
router = APIRouter()

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg", "audio/mp4", "audio/wav", "audio/webm",
    "audio/ogg", "audio/flac", "audio/m4a",
}
MAX_AUDIO_MB = 25
WHISPER_URL = "https://openrouter.ai/api/v1/audio/transcriptions"


async def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API via openrouter.ai.
    Returns transcribed text or raises HTTPException.
    """
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Voice transcription not available (API key not configured)",
        )

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            WHISPER_URL,
            headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
            files={"file": (filename, audio_bytes, "audio/mpeg")},
            data={"model": "openai/whisper-1"},
        )
        if response.status_code != 200:
            logger.error(f"Whisper API error: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=502,
                detail="Voice transcription failed. Please try typing your message.",
            )
        data = response.json()
        return data.get("text", "").strip()


@router.post("/transcribe")
async def voice_to_chat(
    session_id: str,
    audio: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    EN-01: Voice input endpoint.
    1. Accepts audio upload (mp3, wav, webm, ogg, flac, m4a)
    2. Transcribes with Whisper
    3. Routes through the multi-agent pipeline
    4. Returns transcription + agent response
    """
    # Validate content type
    if audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Audio format not supported. Accepted: mp3, wav, webm, ogg, flac, m4a",
        )

    audio_bytes = await audio.read()
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > MAX_AUDIO_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds {MAX_AUDIO_MB} MB limit",
        )

    logger.info(f"Voice input: {size_mb:.2f}MB from session {session_id}")

    # Transcribe
    transcribed_text = await transcribe_audio(audio_bytes, audio.filename or "audio.mp3")
    if not transcribed_text:
        raise HTTPException(
            status_code=422,
            detail="Could not transcribe audio. Please speak clearly or type your message.",
        )

    logger.info(f"Transcribed: '{transcribed_text}' for session {session_id}")

    # Route through agent pipeline (same as chat endpoint)
    db = get_db()
    user_id = str(user["_id"])
    existing = await db.sessions.find_one({"session_id": session_id})
    if not existing:
        await create_session(user_id, session_id, transcribed_text)

    history = await get_history(session_id, last_n=10)
    await append_turn(session_id, "user", transcribed_text)

    import time
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
