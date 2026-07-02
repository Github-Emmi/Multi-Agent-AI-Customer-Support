"""
EN-06: Webhook integration for Email and WhatsApp channels.
Receives inbound messages from external services, routes them through
the multi-agent pipeline, and sends the response back.

Supported channels:
- Email webhooks (e.g. Mailgun, SendGrid Inbound Parse)
- WhatsApp webhooks (e.g. Twilio WhatsApp, WhatsApp Business API)
"""
import hashlib
import hmac
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from typing import Optional
import uuid

from backend.agents.router import run_agents
from backend.database.conversation import create_session, append_turn, get_history
from backend.database.mongo import get_db
from backend.config import settings
from backend.services.email import send_ticket_confirmation_email

logger = logging.getLogger("techmart.webhooks")
router = APIRouter()

# ── Inbound Email Webhook ─────────────────────────────────────────────────────

@router.post("/email/inbound")
async def email_inbound(request: Request):
    """
    Receive inbound customer email via Mailgun / SendGrid Inbound Parse.
    Parse the message, route it to the multi-agent pipeline, and store the reply.
    The email reply is handled separately by the email service.
    """
    try:
        form = await request.form()
        sender = str(form.get("sender") or form.get("from", ""))
        subject = str(form.get("subject", "Support Request"))
        body = str(form.get("stripped-text") or form.get("text", ""))

        if not sender or not body.strip():
            return {"status": "ignored", "reason": "Empty sender or body"}

        # Create a deterministic session ID based on sender email
        session_id = f"email_{hashlib.md5(sender.encode()).hexdigest()[:12]}"

        logger.info(f"Inbound email from {sender} | subject: {subject}")

        db = get_db()
        existing = await db.sessions.find_one({"session_id": session_id})
        if not existing:
            await create_session(sender, session_id, subject)

        history = await get_history(session_id, last_n=10)
        await append_turn(session_id, "user", body)

        result = await run_agents(
            query=body,
            session_id=session_id,
            conversation_history=history,
        )

        response_text = result.get("final_response", "")
        agents_used = result.get("agents_used", [])

        await append_turn(
            session_id=session_id,
            role="assistant",
            content=response_text,
            agents_used=agents_used,
            response_time_ms=result.get("response_time_ms", 0),
        )

        logger.info(f"Email response generated for {sender} via agents {agents_used}")
        return {"status": "processed", "session_id": session_id, "agents": agents_used}

    except Exception as exc:
        logger.error(f"Email webhook error: {exc}")
        return {"status": "error", "detail": str(exc)}


# ── WhatsApp Webhook ──────────────────────────────────────────────────────────

@router.get("/whatsapp")
async def whatsapp_verify(
    request: Request,
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None,
):
    """
    WhatsApp Business API webhook verification (GET request from Meta).
    Set WHATSAPP_VERIFY_TOKEN in .env to match your Meta App settings.
    """
    verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "techmart_verify_token")
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("WhatsApp webhook verified")
        return int(hub_challenge) if hub_challenge else 0
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/whatsapp")
async def whatsapp_inbound(request: Request):
    """
    Receive inbound WhatsApp messages via Meta Cloud API / Twilio.
    Routes through the multi-agent pipeline and stores the response.
    The actual WhatsApp reply is sent via the WhatsApp API separately.
    """
    try:
        payload = await request.json()
        # Meta Cloud API structure
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no_messages"}

        message = messages[0]
        from_number = message.get("from", "")
        msg_type = message.get("type", "")
        text_body = ""

        if msg_type == "text":
            text_body = message.get("text", {}).get("body", "")
        elif msg_type == "audio":
            logger.info(f"WhatsApp audio from {from_number} — voice transcription needed")
            return {"status": "audio_not_supported"}
        else:
            return {"status": "unsupported_type", "type": msg_type}

        if not text_body.strip():
            return {"status": "empty_message"}

        session_id = f"wa_{hashlib.md5(from_number.encode()).hexdigest()[:12]}"
        logger.info(f"WhatsApp message from {from_number}: '{text_body[:60]}'")

        db = get_db()
        existing = await db.sessions.find_one({"session_id": session_id})
        if not existing:
            await create_session(from_number, session_id, text_body)

        history = await get_history(session_id, last_n=10)
        await append_turn(session_id, "user", text_body)

        result = await run_agents(
            query=text_body,
            session_id=session_id,
            conversation_history=history,
        )

        response_text = result.get("final_response", "")
        agents_used = result.get("agents_used", [])

        await append_turn(
            session_id=session_id,
            role="assistant",
            content=response_text,
            agents_used=agents_used,
            response_time_ms=result.get("response_time_ms", 0),
        )

        logger.info(f"WhatsApp response generated for {from_number}")
        return {
            "status": "processed",
            "session_id": session_id,
            "response": response_text,
            "agents": agents_used,
        }

    except Exception as exc:
        logger.error(f"WhatsApp webhook error: {exc}")
        return {"status": "error", "detail": str(exc)}
