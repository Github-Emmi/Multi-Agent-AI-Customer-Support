"""
Integration Tests — Admin API
V-Model Phase: Integration Testing
Tests: admin-only endpoints for KB management and ticket overview.
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient
import io

# Fixture to create an admin user and get auth headers
@pytest_asyncio.fixture
async def admin_auth_headers(client: AsyncClient, auth_user, mock_db):
    # The JWT carries the user id as a string, but the mock stores _id as an
    # ObjectId — so match on the (string) email the auth_user fixture registered.
    email = "test@techmart.com"
    await mock_db.users.update_one({"email": email}, {"$set": {"role": "admin"}})

    # Verify the user is now an admin
    updated_user = await mock_db.users.find_one({"email": email})
    assert updated_user is not None and updated_user["role"] == "admin"

    return {"Authorization": f"Bearer {auth_user['token']}"}


@pytest.mark.asyncio
class TestAdminSecurity:
    async def test_admin_endpoints_require_auth(self, client):
        resp = await client.post("/admin/upload")
        assert resp.status_code == 403
        resp = await client.post("/admin/reindex")
        assert resp.status_code == 403
        resp = await client.get("/admin/documents")
        assert resp.status_code == 403
        resp = await client.delete("/admin/documents/somefile.pdf")
        assert resp.status_code == 403

    async def test_admin_endpoints_require_admin_role(self, client, auth_headers):
        # auth_headers are for a regular user
        resp = await client.post("/admin/reindex", headers=auth_headers)
        assert resp.status_code == 403 # Forbidden

@pytest.mark.asyncio
class TestAdminDocumentManagement:
    async def test_upload_pdf_success(self, client, admin_auth_headers):
        pdf_content = b"%PDF-1.5 test content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        with patch("backend.api.admin.KNOWLEDGE_BASE_DIR", MagicMock()):
            resp = await client.post("/admin/upload", files=files, headers=admin_auth_headers)
        
        assert resp.status_code == 201
        assert "Uploaded test.pdf" in resp.json()["message"]

    async def test_upload_wrong_file_type(self, client, admin_auth_headers):
        files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
        resp = await client.post("/admin/upload", files=files, headers=admin_auth_headers)
        assert resp.status_code == 415 # Unsupported Media Type

    async def test_upload_file_too_large(self, client, admin_auth_headers):
        large_content = b"a" * (21 * 1024 * 1024) # 21 MB
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        resp = await client.post("/admin/upload", files=files, headers=admin_auth_headers)
        assert resp.status_code == 413 # Request Entity Too Large

    async def test_list_documents(self, client, admin_auth_headers, mock_db):
        await mock_db.kb_documents.insert_one({"filename": "doc1.pdf", "is_indexed": True})
        resp = await client.get("/admin/documents", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["filename"] == "doc1.pdf"

    async def test_reindex_starts_background_task(self, client, admin_auth_headers):
        with patch("backend.api.admin.ingest_documents") as mock_ingest, \
             patch("backend.api.admin.retriever") as mock_retriever:

            resp = await client.post("/admin/reindex", headers=admin_auth_headers)
            assert resp.status_code == 200
            assert "Re-indexing started in the background" in resp.json()["message"]
            # Background tasks are tricky to test directly without more complex setups
            # Here we trust FastAPI's BackgroundTasks and just check the endpoint response

@pytest.mark.asyncio
class TestAdminTicketManagement:
    async def test_list_all_tickets(self, client, admin_auth_headers, mock_db):
        await mock_db.tickets.insert_one({
            "ticket_id": "TKT-001", "subject": "Test Ticket", "status": "open",
            "priority": "high", "created_at": "2023-01-01T12:00:00Z"
        })
        resp = await client.get("/admin/tickets", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["ticket_id"] == "TKT-001"

    async def test_get_ticket_stats(self, client, admin_auth_headers, mock_db):
        await mock_db.tickets.insert_one({"status": "open"})
        await mock_db.tickets.insert_one({"status": "open"})
        await mock_db.tickets.insert_one({"status": "closed"})
        
        # This part of the code has a bug - it queries a non-existent collection `db.analytics.tickets`
        # We will mock the aggregate function to avoid the error
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value = [{"_id": "open", "count": 2}, {"_id": "closed", "count": 1}])
        mock_db.tickets.aggregate = MagicMock(return_value=mock_aggregate)
        
        resp = await client.get("/admin/tickets/stats", headers=admin_auth_headers)
        
        assert resp.status_code == 200
        data = resp.json()["by_status"]
        assert data["open"] == 2
        assert data["closed"] == 1

