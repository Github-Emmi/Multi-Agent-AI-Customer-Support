"""
Local intent router (the "Kaggle Factory" lightweight-inference artifact).

Replaces the per-query LLM call for intent detection with a fast, free,
fine-tuned DistilBERT classifier trained offline on Banking77 + CFPB and mapped
to the five agent domains. This removes the main source of OpenRouter 429s and
cuts routing latency from a network round-trip to a local forward pass.

The artifact lives at settings.INTENT_MODEL_PATH. If it is missing or fails to
load, the loader stays None so callers can fall back to the LLM path — the app
never crashes just because the artifact hasn't been downloaded yet.
"""
import logging
import re
from typing import List, Optional

from backend.config import settings

logger = logging.getLogger("techmart.intent")

INTENT_LABELS = ["billing", "technical", "product", "complaint", "faq"]

# Words that signal frustration — used by the local sentiment heuristic so that
# "local" routing mode makes ZERO LLM calls.
_FRUSTRATION_TERMS = {
    "angry", "furious", "terrible", "worst", "unacceptable", "ridiculous",
    "scam", "fraud", "useless", "horrible", "disgusted", "outrageous",
    "never", "again", "refund now", "cancel", "sue", "complaint", "complain",
}


class LocalIntentClassifier:
    """Thin wrapper around a HuggingFace text-classification pipeline."""

    def __init__(self, model_path: str, threshold: float):
        self.threshold = threshold
        self._pipe = None
        self._load(model_path)

    def _load(self, model_path: str) -> None:
        import os

        # Require the actual model config, not just the directory — the folder
        # ships with only a README until the Kaggle artifact is dropped in.
        if not os.path.isfile(os.path.join(model_path, "config.json")):
            logger.warning(
                "Intent classifier artifact not found at '%s' — "
                "routing will fall back to the LLM.", model_path
            )
            return
        try:
            # Imported lazily: transformers is only needed when the local
            # artifact is actually present.
            from transformers import pipeline

            self._pipe = pipeline(
                "text-classification",
                model=model_path,
                tokenizer=model_path,
                top_k=None,  # return scores for every label
            )
            logger.info("Local intent classifier loaded from '%s'.", model_path)
        except Exception as exc:  # pragma: no cover - env dependent
            logger.warning(
                "Failed to load intent classifier (%s) — falling back to LLM.",
                exc,
            )
            self._pipe = None

    @property
    def available(self) -> bool:
        return self._pipe is not None

    @staticmethod
    def _normalize_label(raw: str) -> Optional[str]:
        """Map a raw model label to one of INTENT_LABELS."""
        label = str(raw).lower().strip()
        if label in INTENT_LABELS:
            return label
        # Handle default HuggingFace "LABEL_0" style ids by position.
        m = re.fullmatch(r"label_(\d+)", label)
        if m:
            idx = int(m.group(1))
            if 0 <= idx < len(INTENT_LABELS):
                return INTENT_LABELS[idx]
        return None

    def classify(self, query: str) -> List[str]:
        """Return the domains scoring above the confidence threshold."""
        if not self._pipe:
            return []

        raw = self._pipe(query)
        # pipeline(..., top_k=None) returns a list of {label, score} dicts,
        # sometimes nested one level deep depending on the transformers version.
        if raw and isinstance(raw[0], list):
            raw = raw[0]

        scored = []
        for item in raw:
            label = self._normalize_label(item.get("label", ""))
            if label and item.get("score", 0.0) >= self.threshold:
                scored.append((label, item["score"]))

        scored.sort(key=lambda x: x[1], reverse=True)
        # De-duplicate while preserving score order.
        seen, intents = set(), []
        for label, _ in scored:
            if label not in seen:
                seen.add(label)
                intents.append(label)
        return intents


# Module-level singleton, loaded once at import time.
intent_classifier: Optional[LocalIntentClassifier] = None
if settings.ROUTING_MODE == "local":
    intent_classifier = LocalIntentClassifier(
        settings.INTENT_MODEL_PATH,
        settings.INTENT_CONFIDENCE_THRESHOLD,
    )


def local_frustration_score(query: str) -> int:
    """Fast keyword-based frustration score (1-5) — no LLM call.

    Used only in local routing mode to decide whether to inject the complaint
    agent, keeping the routing hot path completely LLM-free.
    """
    text = query.lower()
    hits = sum(1 for term in _FRUSTRATION_TERMS if term in text)
    exclaims = text.count("!")
    caps_words = sum(1 for w in query.split() if len(w) > 2 and w.isupper())
    raw = hits + (exclaims >= 2) + (caps_words >= 1)
    return max(1, min(5, 2 + raw))
