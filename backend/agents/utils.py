"""Shared utilities for all agent modules."""
from typing import List


def format_history(history: List[dict], last_n: int = 5) -> str:
    """Format the last N conversation turns into a readable string for LLM context."""
    if not history:
        return "No previous conversation."
    lines = []
    for turn in history[-last_n:]:
        role = "Customer" if turn.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {turn.get('content', '')}")
    return "\n".join(lines)
