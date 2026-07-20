"""
Admin API — /admin/*
Knowledge base PDF upload and re-indexing. Admin role required.
"""
import asyncio
import os
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, status

from backend.api.auth import require_admin
from backend.database.mongo import get_db
from backend.rag.pipeline import ingest_documents
from backend.rag.retriever import retriever

KNOWLEDGE_BASE_DIR = Path("knowledge_base")
MAX_FILE_SIZE_MB = 20
ALLOWED_MIME = {"application/pdf"}

router = APIRouter()


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin),
):
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted",
        )

    # Read and validate size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit",
        )

    # Sanitise filename — strip path traversal characters
    safe_name = Path(file.filename).name
    if ".." in safe_name or "/" in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    dest = KNOWLEDGE_BASE_DIR / safe_name
    KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)
    with open(dest, "wb") as f:
        f.write(contents)

    # Register in db
    db = get_db()
    await db.kb_documents.update_one(
        {"filename": safe_name},
        {
            "$set": {
                "filename": safe_name,
                "original_name": file.filename,
                "uploaded_by": str(admin["_id"]),
                "uploaded_at": datetime.utcnow(),
                "file_size_bytes": len(contents),
                "is_indexed": False,
            }
        },
        upsert=True,
    )

    return {"message": f"Uploaded {safe_name} ({size_mb:.2f} MB). Run /admin/reindex to update the knowledge base."}


@router.post("/reindex")
async def reindex_knowledge_base(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(require_admin),
):
    async def _run_ingest():
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, ingest_documents)
            retriever.reload()
            db = get_db()
            await db.kb_documents.update_many(
                {},
                {"$set": {"is_indexed": True, "last_indexed_at": datetime.utcnow()}},
            )
        except Exception as exc:
            # Log and swallow — background task cannot raise HTTP exceptions
            print(f"[reindex] ERROR: {exc}")

    background_tasks.add_task(_run_ingest)
    return {"message": "Re-indexing started in the background. Check /admin/documents for status."}


@router.get("/documents")
async def list_documents(admin: dict = Depends(require_admin)):
    db = get_db()
    docs = await db.kb_documents.find({}).to_list(100)
    return [
        {
            "filename": d["filename"],
            "file_size_bytes": d.get("file_size_bytes"),
            "is_indexed": d.get("is_indexed", False),
            "uploaded_at": d.get("uploaded_at"),
            "last_indexed_at": d.get("last_indexed_at"),
        }
        for d in docs
    ]


@router.delete("/documents/{filename}")
async def delete_document(
    filename: str,
    admin: dict = Depends(require_admin),
):
    # Sanitise
    safe_name = Path(filename).name
    if ".." in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    dest = KNOWLEDGE_BASE_DIR / safe_name
    if not dest.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    dest.unlink()

    db = get_db()
    await db.kb_documents.delete_one({"filename": safe_name})

    # Trigger re-index after deletion (non-blocking)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, ingest_documents)
    retriever.reload()

    return {"message": f"{safe_name} deleted and index updated"}


# ── EN-08: Admin Ticket Management ───────────────────────────────────────────

@router.get("/tickets")
async def list_all_tickets(
    status: str = None,
    priority: str = None,
    limit: int = 50,
    admin: dict = Depends(require_admin),
):
    """List all tickets with optional status/priority filter."""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority

    tickets = await db.tickets.find(query).sort(
        "created_at", -1
    ).limit(limit).to_list(limit)

    return [
        {
            "ticket_id": t["ticket_id"],
            "user_name": t.get("user_name"),
            "user_email": t.get("user_email"),
            "subject": t["subject"],
            "status": t["status"],
            "priority": t["priority"],
            "handoff": t.get("handoff", False),
            "assigned_agent": t.get("assigned_agent"),
            "created_at": t["created_at"],
        }
        for t in tickets
    ]


@router.get("/tickets/stats")
async def ticket_stats(admin: dict = Depends(require_admin)):
    """Summary of ticket counts by status."""
    db = get_db()
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    results = await db.tickets.aggregate(pipeline).to_list(10)
    return {"by_status": {r["_id"]: r["count"] for r in results}}
