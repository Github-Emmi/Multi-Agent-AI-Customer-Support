"""
EN-07: AI-generated conversation summaries.
Generates a concise summary of a completed conversation using the LLM.
Called automatically when a session is closed/deleted or via explicit API trigger.
"""
import logging
from typing import List
from langchain_openai import ChatOpenAI
from backend.config import settings

logger = logging.getLogger("techmart.summarizer")

SUMMARY_PROMPT = """You are a customer support quality analyst for TechMart Electronics.
Read the conversation below and produce a brief structured summary.

Format your response EXACTLY as:
ISSUE: <one sentence describing the customer's problem>
AGENTS: <comma-separated list of agents involved>
RESOLUTION: <one sentence on whether and how it was resolved>
SENTIMENT: <positive | neutral | frustrated | angry>
ACTION_REQUIRED: <yes | no> — yes if an unresolved issue needs follow-up

Conversation:
{conversation}
"""


def _format_conversation(turns: List[dict]) -> str:
    """Convert turns list into readable dialogue string."""
    lines = []
    for turn in turns:
        role = "Customer" if turn.get("role") == "user" else "TechMart AI"
        lines.append(f"{role}: {turn.get('content', '')}")
    return "\n".join(lines)


async def generate_summary(session_id: str, turns: List[dict]) -> dict:
    """
    Generate a structured summary for a completed conversation.
    Returns a dict with keys: issue, agents, resolution, sentiment, action_required, summary_text.
    """
    if not turns:
        return {"summary_text": "No conversation content to summarize."}

    if not settings.OPENROUTER_API_KEY:
        logger.warning("No OPENROUTER_API_KEY — skipping summary generation")
        return {"summary_text": "Summary unavailable (LLM not configured)."}

    conversation_text = _format_conversation(turns)

    try:
        llm = ChatOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            max_tokens=300,
        )
        response = llm.invoke(
            SUMMARY_PROMPT.format(conversation=conversation_text)
        ).content.strip()

        # Parse structured response
        parsed = {"summary_text": response, "session_id": session_id}
        for line in response.split("\n"):
            if line.startswith("ISSUE:"):
                parsed["issue"] = line.replace("ISSUE:", "").strip()
            elif line.startswith("AGENTS:"):
                agents_str = line.replace("AGENTS:", "").strip()
                parsed["agents"] = [a.strip() for a in agents_str.split(",")]
            elif line.startswith("RESOLUTION:"):
                parsed["resolution"] = line.replace("RESOLUTION:", "").strip()
            elif line.startswith("SENTIMENT:"):
                parsed["sentiment"] = line.replace("SENTIMENT:", "").strip().lower()
            elif line.startswith("ACTION_REQUIRED:"):
                val = line.replace("ACTION_REQUIRED:", "").strip().lower()
                parsed["action_required"] = val.startswith("yes")

        logger.info(f"Summary generated for session {session_id}")
        return parsed

    except Exception as exc:
        logger.error(f"Summary generation failed for {session_id}: {exc}")
        return {"summary_text": "Summary generation failed.", "session_id": session_id}


async def save_summary(session_id: str, summary: dict) -> None:
    """Persist the summary to MongoDB."""
    from backend.database.mongo import get_db
    from datetime import datetime
    db = get_db()
    await db.conversations.update_one(
        {"session_id": session_id},
        {"$set": {"summary": summary, "summarized_at": datetime.utcnow()}},
    )
    logger.info(f"Summary saved for session {session_id}")
