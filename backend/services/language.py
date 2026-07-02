"""
EN-02: Multilingual conversation support.
Detects the language of the customer's message and instructs the LLM
to respond in the same language.
"""
import logging
from langchain_openai import ChatOpenAI
from backend.config import settings

logger = logging.getLogger("techmart.language")

DETECT_PROMPT = """Detect the language of this text. Return ONLY the ISO 639-1
two-letter language code (e.g. "en", "fr", "es", "de", "zh", "ar", "pt").

Text: {text}

Language code:"""

MULTILINGUAL_INSTRUCTION = (
    "IMPORTANT: The customer is writing in {language_name}. "
    "You MUST respond entirely in {language_name}. "
    "Do not switch to English under any circumstances."
)

LANGUAGE_NAMES = {
    "en": "English", "fr": "French", "es": "Spanish", "de": "German",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish",
    "ru": "Russian", "ja": "Japanese", "zh": "Chinese", "ko": "Korean",
    "ar": "Arabic", "hi": "Hindi", "tr": "Turkish", "vi": "Vietnamese",
    "th": "Thai", "sv": "Swedish", "da": "Danish", "fi": "Finnish",
}


async def detect_language(text: str) -> str:
    """
    Detect the language of a text string.
    Returns ISO 639-1 code (e.g. "en", "fr"). Falls back to "en".
    """
    if not settings.OPENROUTER_API_KEY or not text.strip():
        return "en"

    try:
        llm = ChatOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.0,
            max_tokens=5,
        )
        code = llm.invoke(
            DETECT_PROMPT.format(text=text[:200])
        ).content.strip().lower()[:2]

        return code if code in LANGUAGE_NAMES else "en"
    except Exception as exc:
        logger.debug(f"Language detection fallback to 'en': {exc}")
        return "en"


def get_language_instruction(lang_code: str) -> str:
    """
    Return an instruction string to inject into the agent system prompt
    if the language is not English.
    """
    if lang_code == "en":
        return ""
    lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
    return MULTILINGUAL_INSTRUCTION.format(language_name=lang_name)


def get_language_name(lang_code: str) -> str:
    return LANGUAGE_NAMES.get(lang_code, lang_code.upper())
