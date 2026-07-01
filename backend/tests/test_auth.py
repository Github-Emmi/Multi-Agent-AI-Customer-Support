"""
Unit Tests — Authentication API
V-Model Phase: Unit Testing (Right Side)
Tests: register, login, logout, password reset, JWT validation
"""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client):
        resp = await client.post("/auth/register", json={
            "name": "Jane Smith",
            "email": "jane@techmart.com",
            "password": "SecurePass1!",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "token" in data
        assert data["name"] == "Jane Smith"
        assert data["role"] == "user"

    async def test_register_duplicate_email(self, client):
        payload = {
            "name": "John Doe",
            "email": "dup@techmart.com",
            "password": "Password1!",
        }
        await client.post("/auth/register", json=payload)
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_missing_fields(self, client):
        resp = await client.post("/auth/register", json={
            "email": "bad@techmart.com",
        })
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client):
        resp = await client.post("/auth/register", json={
            "name": "Bad Email",
            "email": "not-an-email",
            "password": "Password1!",
        })
        assert resp.status_code == 422

    async def test_register_short_password(self, client):
        resp = await client.post("/auth/register", json={
            "name": "Short Pass",
            "email": "short@techmart.com",
            "password": "abc",
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client):
        await client.post("/auth/register", json={
            "name": "Login User",
            "email": "login@techmart.com",
            "password": "Password1!",
        })
        resp = await client.post("/auth/login", json={
            "email": "login@techmart.com",
            "password": "Password1!",
        })
        assert resp.status_code == 200
        assert "token" in resp.json()

    async def test_login_wrong_password(self, client):
        await client.post("/auth/register", json={
            "name": "Wrong Pass",
            "email": "wrong@techmart.com",
            "password": "Password1!",
        })
        resp = await client.post("/auth/login", json={
            "email": "wrong@techmart.com",
            "password": "WrongPassword99!",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/auth/login", json={
            "email": "ghost@techmart.com",
            "password": "Password1!",
        })
        assert resp.status_code == 401

    async def test_login_returns_correct_fields(self, client):
        await client.post("/auth/register", json={
            "name": "Field Check",
            "email": "fields@techmart.com",
            "password": "Password1!",
        })
        resp = await client.post("/auth/login", json={
            "email": "fields@techmart.com",
            "password": "Password1!",
        })
        data = resp.json()
        assert set(data.keys()) >= {"token", "user_id", "name", "role"}


@pytest.mark.asyncio
class TestProtectedEndpoints:
    async def test_get_me_authenticated(self, client, auth_headers):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@techmart.com"
        assert data["name"] == "Test User"

    async def test_get_me_unauthenticated(self, client):
        resp = await client.get("/auth/me")
        assert resp.status_code == 403

    async def test_get_me_invalid_token(self, client):
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer fake.invalid.token"},
        )
        assert resp.status_code == 401

    async def test_logout_authenticated(self, client, auth_headers):
        resp = await client.post("/auth/logout", headers=auth_headers)
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestPasswordReset:
    async def test_reset_request_always_200(self, client):
        # Should return 200 even for non-existent email (prevents enumeration)
        resp = await client.post(
            "/auth/reset-password",
            json={"email": "unknown@techmart.com"},
        )
        assert resp.status_code == 200

    async def test_reset_full_flow(self, client):
        await client.post("/auth/register", json={
            "name": "Reset User",
            "email": "reset@techmart.com",
            "password": "OldPass1!",
        })
        reset_resp = await client.post(
            "/auth/reset-password",
            json={"email": "reset@techmart.com"},
        )
        assert reset_resp.status_code == 200
        token = reset_resp.json().get("dev_token")
        if not token:
            pytest.skip("dev_token not returned (production mode)")

        confirm_resp = await client.put(
            "/auth/reset-password/confirm",
            json={"token": token, "new_password": "NewPass1!"},
        )
        assert confirm_resp.status_code == 200

        login_resp = await client.post("/auth/login", json={
            "email": "reset@techmart.com",
            "password": "NewPass1!",
        })
        assert login_resp.status_code == 200
