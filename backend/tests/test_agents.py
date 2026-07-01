"""
Unit Tests — Intent Detection & Agent Routing
V-Model Phase: Unit Testing + Integration Testing
Tests: intent classification accuracy, multi-intent routing, sentiment escalation
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ── Intent detection unit tests ───────────────────────────────────────────────

@pytest.mark.asyncio
class TestIntentDetection:
    """Test the intent detect_intent node in isolation."""

    def _make_state(self, query: str) -> dict:
        return {
            "query": query,
            "session_id": "test_session",
            "conversation_history": [],
            "intents": [],
            "sentiment_score": 1,
            "retrieved_contexts": {},
            "agent_responses": [],
            "final_response": "",
            "agents_used": [],
            "response_time_ms": 0,
        }

    def _mock_llm_intent(self, intent_json: str, sentiment: str = "2"):
        mock_llm = MagicMock()
        call_count = [0]

        def side_effect(prompt):
            call_count[0] += 1
            resp = MagicMock()
            # First call = intent, second call = sentiment
            resp.content = intent_json if call_count[0] == 1 else sentiment
            return resp

        mock_llm.invoke = side_effect
        return mock_llm

    async def test_billing_intent(self):
        from backend.agents.router import detect_intent
        with patch("backend.agents.router.get_llm",
                   return_value=self._mock_llm_intent('["billing"]')):
            state = self._make_state("I need a refund for my order")
            result = detect_intent(state)
            assert "billing" in result["intents"]

    async def test_technical_intent(self):
        from backend.agents.router import detect_intent
        with patch("backend.agents.router.get_llm",
                   return_value=self._mock_llm_intent('["technical"]')):
            state = self._make_state("I cannot log into my account")
            result = detect_intent(state)
            assert "technical" in result["intents"]

    async def test_multi_intent_routing(self):
        from backend.agents.router import detect_intent
        with patch("backend.agents.router.get_llm",
                   return_value=self._mock_llm_intent('["billing", "technical"]')):
            state = self._make_state("I paid but Premium is still locked")
            result = detect_intent(state)
            assert "billing" in result["intents"]
            assert "technical" in result["intents"]

    async def test_invalid_intent_falls_back_to_faq(self):
        from backend.agents.router import detect_intent
        with patch("backend.agents.router.get_llm",
                   return_value=self._mock_llm_intent("not valid json")):
            state = self._make_state("Hello")
            result = detect_intent(state)
            assert result["intents"] == ["faq"]

    async def test_high_sentiment_adds_complaint(self):
        """Frustration score >= 4 should inject complaint agent."""
        from backend.agents.router import detect_intent
        with patch("backend.agents.router.get_llm",
                   return_value=self._mock_llm_intent('["billing"]', "5")):
            state = self._make_state("I am FURIOUS about this billing mistake!!!")
            result = detect_intent(state)
            assert "complaint" in result["intents"]
            assert result["sentiment_score"] == 5

    async def test_low_sentiment_no_complaint_injection(self):
        from backend.agents.router import detect_intent
        with patch("backend.agents.router.get_llm",
                   return_value=self._mock_llm_intent('["faq"]', "1")):
            state = self._make_state("What are your business hours?")
            result = detect_intent(state)
            assert "complaint" not in result["intents"]


# ── Agent node unit tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAgentNodes:
    """Test each agent node returns a response in agent_responses."""

    def _base_state(self, query: str) -> dict:
        return {
            "query": query,
            "session_id": "test_session",
            "conversation_history": [],
            "intents": [],
            "sentiment_score": 1,
            "retrieved_contexts": {},
            "agent_responses": [],
            "final_response": "",
            "agents_used": [],
            "response_time_ms": 0,
        }

    def _mock_retriever_and_llm(self, agent_module_path: str, response_text: str):
        """Patch retriever and LLM for a specific agent module."""
        mock_chunks = [{"text": "Relevant context chunk", "source": "faq.pdf", "score": 0.1}]
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_chunks)

        mock_llm_response = MagicMock()
        mock_llm_response.content = response_text
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(return_value=mock_llm_response)

        return mock_retriever, mock_llm

    async def test_billing_node(self):
        from backend.agents.billing import billing_node
        mock_r, mock_llm = self._mock_retriever_and_llm(
            "backend.agents.billing", "Your refund will be processed in 5-7 days."
        )
        with patch("backend.agents.billing.retriever", mock_r), \
             patch("backend.agents.billing.ChatOpenAI", return_value=mock_llm):
            state = self._base_state("I want a refund")
            result = billing_node(state)
            assert len(result["agent_responses"]) == 1
            assert result["agent_responses"][0]["agent"] == "billing"
            assert "refund" in result["agent_responses"][0]["response"].lower()

    async def test_technical_node(self):
        from backend.agents.technical import technical_node
        mock_r, mock_llm = self._mock_retriever_and_llm(
            "backend.agents.technical", "Go to techmart.com/login and click Forgot Password."
        )
        with patch("backend.agents.technical.retriever", mock_r), \
             patch("backend.agents.technical.ChatOpenAI", return_value=mock_llm):
            state = self._base_state("How do I reset my password?")
            result = technical_node(state)
            assert len(result["agent_responses"]) == 1
            assert result["agent_responses"][0]["agent"] == "technical"

    async def test_faq_node(self):
        from backend.agents.faq import faq_node
        mock_r, mock_llm = self._mock_retriever_and_llm(
            "backend.agents.faq", "Our business hours are Mon-Fri 8 AM - 8 PM EST."
        )
        with patch("backend.agents.faq.retriever", mock_r), \
             patch("backend.agents.faq.ChatOpenAI", return_value=mock_llm):
            state = self._base_state("What are your business hours?")
            result = faq_node(state)
            assert result["agent_responses"][0]["agent"] == "faq"

    async def test_product_node(self):
        from backend.agents.product import product_node
        mock_r, mock_llm = self._mock_retriever_and_llm(
            "backend.agents.product", "The UltraBook 13 has 16 GB RAM and a 512 GB SSD."
        )
        with patch("backend.agents.product.retriever", mock_r), \
             patch("backend.agents.product.ChatOpenAI", return_value=mock_llm):
            state = self._base_state("What are the specs of the UltraBook?")
            result = product_node(state)
            assert result["agent_responses"][0]["agent"] == "product"

    async def test_complaint_node(self):
        from backend.agents.complaint import complaint_node
        mock_r, mock_llm = self._mock_retriever_and_llm(
            "backend.agents.complaint",
            "I understand your frustration. Let me escalate this for you."
        )
        with patch("backend.agents.complaint.retriever", mock_r), \
             patch("backend.agents.complaint.ChatOpenAI", return_value=mock_llm):
            state = self._base_state("This is unacceptable!")
            result = complaint_node(state)
            assert result["agent_responses"][0]["agent"] == "complaint"


# ── Response aggregator tests ─────────────────────────────────────────────────

class TestAggregator:
    def test_single_agent_response(self):
        from backend.agents.router import aggregate_responses
        state = {
            "agent_responses": [{"agent": "billing", "response": "Your refund is approved."}],
            "final_response": "",
            "agents_used": [],
        }
        result = aggregate_responses(state)
        assert result["final_response"] == "Your refund is approved."
        assert result["agents_used"] == ["billing"]

    def test_multi_agent_merges_with_headers(self):
        from backend.agents.router import aggregate_responses
        state = {
            "agent_responses": [
                {"agent": "billing", "response": "Billing answer."},
                {"agent": "technical", "response": "Tech answer."},
            ],
            "final_response": "",
            "agents_used": [],
        }
        result = aggregate_responses(state)
        assert "**Billing Team:**" in result["final_response"]
        assert "**Technical Team:**" in result["final_response"]
        assert "billing" in result["agents_used"]
        assert "technical" in result["agents_used"]

    def test_empty_responses_returns_fallback(self):
        from backend.agents.router import aggregate_responses
        state = {
            "agent_responses": [],
            "final_response": "",
            "agents_used": [],
        }
        result = aggregate_responses(state)
        assert result["final_response"] != ""
        assert result["agents_used"] == []
