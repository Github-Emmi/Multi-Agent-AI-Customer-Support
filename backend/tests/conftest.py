"""
conftest.py — Shared pytest fixtures for all backend tests.
Uses AsyncMock and mongomock-motor for DB isolation.
"""
import asyncio
import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.database import mongo as mongo_module


# ── Clean exit workaround ──────────────────────────────────────────────────────
# PyTorch/FAISS can segfault (exit 139) during interpreter shutdown on Apple
# Silicon — see documentations/13_KAGGLE_FACTORY_PATTERN.md, diagnosis #3. The
# tests themselves pass; only the native atexit destructors crash. We hard-exit
# with the real status AFTER pytest (and coverage) have finished so the crash
# cannot mask a green run. Runs last (trylast) so coverage still writes its data.
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    # Only short-circuit a clean run — on failures/errors let pytest exit
    # normally so full tracebacks are still printed.
    if int(exitstatus) == 0:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)


# ── Event loop ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Mock database ─────────────────────────────────────────────────────────────

class MockCollection:
    """In-memory async collection mock."""

    def __init__(self):
        self._data: list[dict] = []

    async def insert_one(self, doc):
        from bson import ObjectId
        doc = dict(doc)
        doc.setdefault("_id", ObjectId())
        self._data.append(doc)
        result = MagicMock()
        result.inserted_id = doc["_id"]
        return result

    async def find_one(self, query):
        for doc in self._data:
            if self._matches(doc, query):
                return doc
        return None

    async def update_one(self, query, update, upsert=False):
        for doc in self._data:
            if self._matches(doc, query):
                if "$set" in update:
                    doc.update(update["$set"])
                if "$push" in update:
                    for k, v in update["$push"].items():
                        doc.setdefault(k, []).append(v)
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        doc[k] = doc.get(k, 0) + v
                return MagicMock(matched_count=1, modified_count=1)
        if upsert:
            from bson import ObjectId
            new_doc = {}
            if "$set" in update:
                new_doc.update(update["$set"])
            if "$setOnInsert" in update:
                new_doc.update(update["$setOnInsert"])
            if "$push" in update:
                for k, v in update["$push"].items():
                    items = v.get("$each", [v]) if isinstance(v, dict) and "$each" in v else [v]
                    new_doc.setdefault(k, []).extend(items)
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    new_doc[k] = new_doc.get(k, 0) + v
            for k, v in query.items():
                if not k.startswith("$"):
                    new_doc.setdefault(k, v)
            new_doc.setdefault("_id", ObjectId())
            self._data.append(new_doc)
        return MagicMock(matched_count=0, modified_count=0)

    async def delete_one(self, query):
        before = len(self._data)
        self._data = [d for d in self._data if not self._matches(d, query)]
        return MagicMock(deleted_count=before - len(self._data))

    def find(self, query=None):
        results = [d for d in self._data if not query or self._matches(d, query)]
        mock = MagicMock()
        mock.sort = MagicMock(return_value=mock)
        mock.limit = MagicMock(return_value=mock)

        async def to_list(length=None):
            return results[:length] if length else results
        mock.to_list = to_list
        return mock

    def aggregate(self, pipeline):
        mock = MagicMock()
        async def to_list(length=None):
            return []
        mock.to_list = to_list
        return mock

    async def create_index(self, *args, **kwargs):
        pass

    def _matches(self, doc: dict, query: dict) -> bool:
        for key, val in query.items():
            if key.startswith("$"):
                continue
            if isinstance(val, dict):
                doc_val = doc.get(key)
                if "$gte" in val and doc_val < val["$gte"]:
                    return False
            elif doc.get(key) != val:
                return False
        return True


class MockDB:
    def __init__(self):
        self.users = MockCollection()
        self.sessions = MockCollection()
        self.conversations = MockCollection()
        self.analytics = MockCollection()
        self.tickets = MockCollection()
        self.kb_documents = MockCollection()


@pytest.fixture
def mock_db():
    return MockDB()


@pytest.fixture(autouse=True)
def patch_db(mock_db):
    """Patch get_db() and connect_db() for all tests."""
    with patch.object(mongo_module, "db", mock_db), \
         patch("backend.database.mongo.get_db", return_value=mock_db), \
         patch("backend.database.mongo.connect_db", new_callable=AsyncMock), \
         patch("backend.database.mongo.close_db", new_callable=AsyncMock):
        yield mock_db


# ── HTTP test client ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(patch_db):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ── Auth helpers ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def auth_user(client, patch_db):
    """Register and login a test user, return token."""
    await client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@techmart.com",
        "password": "Password123!",
    })
    resp = await client.post("/auth/login", json={
        "email": "test@techmart.com",
        "password": "Password123!",
    })
    data = resp.json()
    return {"token": data["token"], "user_id": data["user_id"]}


@pytest_asyncio.fixture
async def auth_headers(auth_user):
    return {"Authorization": f"Bearer {auth_user['token']}"}
