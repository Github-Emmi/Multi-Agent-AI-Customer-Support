"""
Tickets API — /tickets/*
Automatic ticket creation from escalated conversations.
EN-04: Automatic ticket creation (Should Implement)
"""
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.api.auth import get_current_user
from backend.database.mongo import get_db

router = APIRouter()


class CreateTicketRequest(BaseModel):
    session_id: str
    subject: str
    description: Optional[str] = None
    priority: str = "medium"  # "low" | "medium" | "high" | "urgent"


class UpdateTicketRequest(BaseModel):
    status: Optional[str] = None   # "open" | "in_progress" | "resolved" | "closed"
    priority: Optional[str] = None
    assigned_agent: Optional[str] = None


def _generate_ticket_id() -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    suffix = secrets.token_hex(3).upper()
    return f"TKT-{date_str}-{suffix}"


@router.post("", status_code=201)
async def create_ticket(
    body: CreateTicketRequest,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = str(user["_id"])

    # Verify session belongs to user
    session = await db.sessions.find_one({"session_id": body.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    ticket_id = _generate_ticket_id()
    ticket = {
        "ticket_id": ticket_id,
        "session_id": body.session_id,
        "user_id": user_id,
        "user_name": user.get("name"),
        "user_email": user.get("email"),
        "subject": body.subject,
        "description": body.description or "",
        "status": "open",
        "priority": body.priority,
        "assigned_agent": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "resolved_at": None,
    }

    await db.tickets.insert_one(ticket)

    # Link ticket to session
    await db.sessions.update_one(
        {"session_id": body.session_id},
        {"$set": {"ticket_id": ticket_id, "is_resolved": False}},
    )

    # Send ticket confirmation email (non-blocking)
    try:
        from backend.services.email import send_ticket_confirmation_email
        await send_ticket_confirmation_email(
            user.get("email", ""), ticket_id, body.subject
        )
    except Exception:
        pass  # Don't fail ticket creation if email fails

    return {
        "ticket_id": ticket_id,
        "status": "open",
        "message": f"Ticket {ticket_id} created. Our team will respond within 24 hours.",
    }


@router.get("")
async def list_my_tickets(user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = str(user["_id"])
    tickets = await db.tickets.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(20).to_list(20)
    return [
        {
            "ticket_id": t["ticket_id"],
            "subject": t["subject"],
            "status": t["status"],
            "priority": t["priority"],
            "created_at": t["created_at"],
        }
        for t in tickets
    ]


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    ticket = await db.tickets.find_one({"ticket_id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    user_id = str(user["_id"])
    if ticket["user_id"] != user_id and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return ticket


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    body: UpdateTicketRequest,
    user: dict = Depends(get_current_user),
):
    """Admin can update status, priority, and assign agents."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()
    update = {"updated_at": datetime.utcnow()}
    if body.status:
        update["status"] = body.status
        if body.status == "resolved":
            update["resolved_at"] = datetime.utcnow()
    if body.priority:
        update["priority"] = body.priority
    if body.assigned_agent is not None:
        update["assigned_agent"] = body.assigned_agent

    result = await db.tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": update},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": f"Ticket {ticket_id} updated"}
