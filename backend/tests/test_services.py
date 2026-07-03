"""
Unit Tests — Sentiment Analysis + Language Detection + Email Service
V-Model Phase: Unit Testing
Target: boost backend coverage to 80%+
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ── Sentiment Analysis ────────────────────────────────────────────────────────

class TestSentimentAnalysis:
    """Test standalone sentiment module."""

    def _mock_llm_response(self, content: str):
        mock = MagicMock()
        mock.content = content
        llm = MagicMock()
        llm.invoke = MagicMock(return_value=mock)
        return llm

    @pytest.mark.asyncio
    async def test_analyze_positive_sentiment(self):
        from backend.agents.sentiment import analyze_sentiment
        with patch("backend.agents.sentiment.ChatOpenAI",
                   return_value=self._mock_llm_response('{"score": 1, "label": "positive"}')):
            result = await analyze_sentiment("Thank you for your help!")
            assert result["score"] == 1
            assert result["label"] == "positive"

    @pytest.mark.asyncio
    async def test_analyze_frustrated_sentiment(self):
        from backend.agents.sentiment import analyze_sentiment
        with patch("backend.agents.sentiment.ChatOpenAI",
                   return_value=self._mock_llm_response('{"score": 5, "label": "angry"}')):
            result = await analyze_sentiment("This is ABSOLUTELY UNACCEPTABLE!")
            assert result["score"] == 5
            assert result["label"] == "angry"

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_json(self):
        from backend.agents.sentiment import analyze_sentiment
        with patch("backend.agents.sentiment.ChatOpenAI",
                   return_value=self._mock_llm_response("not valid json")):
            result = await analyze_sentiment("test")
            assert result["score"] == 2
            assert result["label"] == "neutral"

    @pytest.mark.asyncio
    async def test_fallback_when_no_api_key(self):
        from backend.agents.sentiment import analyze_sentiment
        with patch("backend.agents.sentiment.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = ""
            result = await analyze_sentiment("test")
            assert result == {"score": 2, "label": "neutral"}

    def test_should_escalate_high_score(self):
        from backend.agents.sentiment import should_escalate
        assert should_escalate({"score": 4}) is True
        assert should_escalate({"score": 5}) is True

    def test_should_not_escalate_low_score(self):
        from backend.agents.sentiment import should_escalate
        assert should_escalate({"score": 1}) is False
        assert should_escalate({"score": 3}) is False

    def test_sentiment_to_priority_mapping(self):
        from backend.agents.sentiment import sentiment_to_priority
        assert sentiment_to_priority({"score": 5}) == "urgent"
        assert sentiment_to_priority({"score": 4}) == "high"
        assert sentiment_to_priority({"score": 3}) == "medium"
        assert sentiment_to_priority({"score": 1}) == "low"

    @pytest.mark.asyncio
    async def test_score_clamped_to_1_5(self):
        from backend.agents.sentiment import analyze_sentiment
        with patch("backend.agents.sentiment.ChatOpenAI",
                   return_value=self._mock_llm_response('{"score": 99, "label": "angry"}')):
            result = await analyze_sentiment("test")
            assert 1 <= result["score"] <= 5


# ── Language Detection ────────────────────────────────────────────────────────

class TestLanguageDetection:
    """Test multilingual service."""

    def _mock_llm(self, lang_code: str):
        mock = MagicMock()
        mock.content = lang_code
        llm = MagicMock()
        llm.invoke = MagicMock(return_value=mock)
        return llm

    @pytest.mark.asyncio
    async def test_detect_english(self):
        from backend.services.language import detect_language
        with patch("backend.services.language.ChatOpenAI",
                   return_value=self._mock_llm("en")):
            code = await detect_language("Hello, I need help.")
            assert code == "en"

    @pytest.mark.asyncio
    async def test_detect_french(self):
        from backend.services.language import detect_language
        with patch("backend.services.language.ChatOpenAI",
                   return_value=self._mock_llm("fr")):
            code = await detect_language("Bonjour, j'ai besoin d'aide.")
            assert code == "fr"

    @pytest.mark.asyncio
    async def test_detect_spanish(self):
        from backend.services.language import detect_language
        with patch("backend.services.language.ChatOpenAI",
                   return_value=self._mock_llm("es")):
            code = await detect_language("Necesito ayuda con mi pedido.")
            assert code == "es"

    @pytest.mark.asyncio
    async def test_unknown_code_falls_back_to_english(self):
        from backend.services.language import detect_language
        with patch("backend.services.language.ChatOpenAI",
                   return_value=self._mock_llm("xx")):
            code = await detect_language("test")
            assert code == "en"

    @pytest.mark.asyncio
    async def test_fallback_when_no_api_key(self):
        from backend.services.language import detect_language
        with patch("backend.services.language.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = ""
            code = await detect_language("Bonjour")
            assert code == "en"

    def test_english_instruction_is_empty(self):
        from backend.services.language import get_language_instruction
        assert get_language_instruction("en") == ""

    def test_non_english_instruction_has_content(self):
        from backend.services.language import get_language_instruction
        instruction = get_language_instruction("fr")
        assert "French" in instruction
        assert len(instruction) > 10

    def test_get_language_name(self):
        from backend.services.language import get_language_name
        assert get_language_name("en") == "English"
        assert get_language_name("fr") == "French"
        assert get_language_name("es") == "Spanish"
        assert get_language_name("zz") == "ZZ"


# ── Email Service ─────────────────────────────────────────────────────────────

class TestEmailService:
    """Test async email service."""

    @pytest.mark.asyncio
    async def test_password_reset_email_dev_mode(self):
        """In dev mode (no SMTP config), email is skipped — returns True."""
        from backend.services.email import send_password_reset_email
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.SMTP_USER = ""
            mock_settings.SMTP_PASS = ""
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            result = await send_password_reset_email("test@example.com", "reset_token_123")
            assert result is True

    @pytest.mark.asyncio
    async def test_ticket_confirmation_email_dev_mode(self):
        from backend.services.email import send_ticket_confirmation_email
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.SMTP_USER = ""
            mock_settings.SMTP_PASS = ""
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            result = await send_ticket_confirmation_email(
                "test@example.com", "TKT-20260703-ABC", "Account access issue"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_email_returns_false_on_smtp_error(self):
        from backend.services.email import send_password_reset_email
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.SMTP_USER = "user@gmail.com"
            mock_settings.SMTP_PASS = "password"
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            # Patch aiosmtplib at the module level where it's imported inside the function
            import sys
            import types
            fake_aiosmtplib = types.ModuleType("aiosmtplib")
            fake_aiosmtplib.send = AsyncMock(side_effect=Exception("Connection refused"))
            with patch.dict(sys.modules, {"aiosmtplib": fake_aiosmtplib}):
                result = await send_password_reset_email("test@example.com", "token123")
                assert result is False


# ── Agent Utils ───────────────────────────────────────────────────────────────

class TestAgentUtils:
    """Test shared agent utility functions."""

    def test_format_history_empty(self):
        from backend.agents.utils import format_history
        result = format_history([])
        assert result == "No previous conversation."

    def test_format_history_single_turn(self):
        from backend.agents.utils import format_history
        turns = [{"role": "user", "content": "Hello"}]
        result = format_history(turns)
        assert "Customer: Hello" in result

    def test_format_history_both_roles(self):
        from backend.agents.utils import format_history
        turns = [
            {"role": "user", "content": "I need help"},
            {"role": "assistant", "content": "I can help you"},
        ]
        result = format_history(turns)
        assert "Customer: I need help" in result
        assert "Assistant: I can help you" in result

    def test_format_history_respects_last_n(self):
        from backend.agents.utils import format_history
        turns = [{"role": "user", "content": f"msg {i}"} for i in range(10)]
        result = format_history(turns, last_n=3)
        assert "msg 9" in result
        assert "msg 0" not in result

    def test_format_history_handles_missing_content(self):
        from backend.agents.utils import format_history
        turns = [{"role": "user"}]  # no content key
        result = format_history(turns)
        assert "Customer:" in result


# ── Summarizer ────────────────────────────────────────────────────────────────

class TestSummarizer:
    """Test conversation summarizer."""

    @pytest.mark.asyncio
    async def test_summary_empty_turns(self):
        from backend.agents.summarizer import generate_summary
        result = await generate_summary("sess_test", [])
        assert "No conversation" in result["summary_text"]

    @pytest.mark.asyncio
    async def test_summary_no_api_key(self):
        from backend.agents.summarizer import generate_summary
        with patch("backend.agents.summarizer.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = ""
            result = await generate_summary("sess_test", [{"role": "user", "content": "test"}])
            assert "unavailable" in result["summary_text"].lower()

    @pytest.mark.asyncio
    async def test_summary_parsed_correctly(self):
        from backend.agents.summarizer import generate_summary
        mock_response = (
            "ISSUE: Customer cannot login\n"
            "AGENTS: technical\n"
            "RESOLUTION: Guided through password reset\n"
            "SENTIMENT: neutral\n"
            "ACTION_REQUIRED: no"
        )
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(return_value=MagicMock(content=mock_response))
        with patch("backend.agents.summarizer.ChatOpenAI", return_value=mock_llm), \
             patch("backend.agents.summarizer.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
            mock_settings.OPENAI_MODEL = "test-model"
            turns = [
                {"role": "user", "content": "I cannot login"},
                {"role": "assistant", "content": "Let me help you reset your password"},
            ]
            result = await generate_summary("sess_001", turns)
            assert result.get("issue") == "Customer cannot login"
            assert result.get("sentiment") == "neutral"
            assert result.get("action_required") is False
