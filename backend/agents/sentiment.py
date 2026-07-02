"""
EN-03: Sentiment analysis as a standalone reusable module.
Used by the agent router for routing and by analytics for tracking.
Returns a score 1-5 and a label.
"""
import logging
from langchain_openai import ChatOpenAI
from backend.config import settings

logger = logging.getLogger("techmart.sentiment")

SENTIMENT_PROMPT = """Analyze the emotional tone of this customer message.

Return a JSON object with exactly two fields:
- "score": integer 1-5 (1=very positive/calm, 3=neutral, 5=very frustrated/angry)
- "label": one of ["positive", "neutral", "dissatisfied", "frustrated", "angry"]

Message: {message}

Return ONLY the JSON object, no explanation."""


async def analyze_sentiment(message: str) -> dict:
    """
    Analyze sentiment of a single customer message.
    Returns: {"score": int, "label": str}
    Falls back to neutral on any failure.
    """
    if not settings.OPENROUTER_API_KEY:
        return {"score": 2, "label": "neutral"}

    try:
        import json
        llm = ChatOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.0,
            max_tokens=50,
        )
        response = llm.invoke(
            SENTIMENT_PROMPT.format(message=message)
        ).content.strip()

        # Strip markdown code fences if present
        cleaned = response.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned)
        score = max(1, min(5, int(result.get("score", 2))))
        label = result.get("label", "neutral")
        return {"score": score, "label": label}

    except Exception as exc:
        logger.debug(f"Sentiment analysis fallback: {exc}")
        return {"score": 2, "label": "neutral"}


def should_escalate(sentiment: dict) -> bool:
    """Return True if the sentiment warrants escalation to Complaint Agent."""
    return sentiment.get("score", 1) >= 4


def sentiment_to_priority(sentiment: dict) -> str:
    """Map sentiment score to ticket priority."""
    score = sentiment.get("score", 2)
    if score == 5:
        return "urgent"
    if score == 4:
        return "high"
    if score == 3:
        return "medium"
    return "low"
