"""
Integration Tests — Chat API end-to-end
V-Model Phase: Integration Testing + System Testing
Tests: full query → intent → agent → response flow via HTTP
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def _make_mock_run_agents(response_text: str, agents: list[str]):
    async def mock_run_agents(query, session_id, conversation_history):
        return {
            "final_response": response_text,
            "agents_used": agents,
            "response_time_ms": 350,
        }
    return mock_run_agents


@pytest.mark.asyncio
class TestChatEndpoint:
    async def test_chat_requires_auth(self, client):
        resp = await client.post("/chat", json={
            "session_id": "sess_001",
            "message": "Hello",
        })
        assert resp.status_code == 403

    async def test_chat_success_billing(self, client, auth_headers):
        mock_agents = _make_mock_run_agents(
            "Your refund will be processed in 5–7 days.",
            ["billing"],
        )
        with patch("backend.api.chat.run_agents", new=mock_agents):
            resp = await client.post(
                "/chat",
                json={"session_id": "sess_billing_001", "message": "I want a refund"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["response"] == "Your refund will be processed in 5–7 days."
        assert "billing" in data["agents_used"]
        assert data["session_id"] == "sess_billing_001"
        assert data["response_time_ms"] >= 0

    async def test_chat_multi_agent_response(self, client, auth_headers):
        mock_agents = _make_mock_run_agents(
            "**Billing Team:**\nPayment confirmed.\n\n**Technical Team:**\nAccount unlocked.",
            ["billing", "technical"],
        )
        with patch("backend.api.chat.run_agents", new=mock_agents):
            resp = await client.post(
                "/chat",
                json={
                    "session_id": "sess_multi_001",
                    "message": "I paid but Premium is still locked",
                },
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["agents_used"]) == 2
        assert "billing" in data["agents_used"]
        assert "technical" in data["agents_used"]

    async def test_chat_empty_message_rejected(self, client, auth_headers):
        resp = await client.post(
            "/chat",
            json={"session_id": "sess_empty", "message": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_chat_persists_to_history(self, client, auth_headers):
        mock_agents = _make_mock_run_agents("FAQ response.", ["faq"])
        with patch("backend.api.chat.run_agents", new=mock_agents):
            await client.post(
                "/chat",
                json={"session_id": "sess_hist_001", "message": "Business hours?"},
                headers=auth_headers,
            )
        hist_resp = await client.get("/history/sess_hist_001", headers=auth_headers)
        assert hist_resp.status_code == 200
        turns = hist_resp.json().get("turns", [])
        assert any(t["role"] == "user" for t in turns)

    async def test_get_sessions(self, client, auth_headers):
        mock_agents = _make_mock_run_agents("OK", ["faq"])
        with patch("backend.api.chat.run_agents", new=mock_agents):
            await client.post(
                "/chat",
                json={"session_id": "sess_list_001", "message": "test"},
                headers=auth_headers,
            )
        resp = await client.get("/chat/sessions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_new_session_returns_id(self, client, auth_headers):
        resp = await client.post("/chat/new-session", headers=auth_headers)
        assert resp.status_code == 200
        assert "session_id" in resp.json()
        assert resp.json()["session_id"].startswith("sess_")


@pytest.mark.asyncio
class TestHistoryEndpoint:
    async def test_history_not_found(self, client, auth_headers):
        resp = await client.get("/history/nonexistent_session", headers=auth_headers)
        assert resp.status_code == 404

    async def test_history_requires_auth(self, client):
        resp = await client.get("/history/sess_xyz")
        assert resp.status_code == 403

    async def test_delete_session(self, client, auth_headers):
        mock_agents = _make_mock_run_agents("OK", ["faq"])
        with patch("backend.api.chat.run_agents", new=mock_agents):
            await client.post(
                "/chat",
                json={"session_id": "sess_del_001", "message": "delete me"},
                headers=auth_headers,
            )
        del_resp = await client.delete("/history/sess_del_001", headers=auth_headers)
        assert del_resp.status_code == 200

        hist_resp = await client.get("/history/sess_del_001", headers=auth_headers)
        assert hist_resp.status_code == 404


@pytest.mark.asyncio
class TestAnalyticsEndpoint:
    async def test_summary_requires_auth(self, client):
        resp = await client.get("/analytics/summary")
        assert resp.status_code == 403

    async def test_summary_returns_structure(self, client, auth_headers):
        resp = await client.get("/analytics/summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_conversations" in data
        assert "avg_response_time_ms" in data
        assert "satisfaction_score" in data

    async def test_agent_usage_returns_list(self, client, auth_headers):
        resp = await client.get("/analytics/agent-usage", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_feedback_submission(self, client, auth_headers):
        resp = await client.post(
            "/analytics/feedback",
            json={"session_id": "sess_fb_001", "rating": 5, "comment": "Excellent!"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    async def test_feedback_rating_validation(self, client, auth_headers):
        resp = await client.post(
            "/analytics/feedback",
            json={"session_id": "sess_fb_002", "rating": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_docs_accessible(self, client):
        resp = await client.get("/docs")
        assert resp.status_code == 200
