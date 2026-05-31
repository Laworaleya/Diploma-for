"""
API AUTH TESTS

Covers registration happy path, login happy path, and
the 401 response when a protected endpoint is called without a token.
"""

from unittest.mock import AsyncMock, patch

from app.core.security import hash_password

FAKE_USER_ID = "507f1f77bcf86cd799439011"


def _make_db_user(email: str = "alice@finlit.test", password: str = "pass1234") -> dict:
    return {
        "id": FAKE_USER_ID,
        "email": email,
        "name": "Alice",
        "hashed_password": hash_password(password),
        "preferred_language": "ru",
        "currency": "KZT",
        "role": "user",
        "created_at": "2025-01-01T00:00:00",
        "is_blocked": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 15. POST /api/auth/register — happy path returns token + user object
# ─────────────────────────────────────────────────────────────────────────────
async def test_register_user_returns_token_and_user_on_happy_path(anon_client):
    created = _make_db_user("newuser@finlit.test", "secure123")

    with patch("app.repositories.user_repo.find_user_by_email", new_callable=AsyncMock, return_value=None), \
         patch("app.repositories.user_repo.create_user",        new_callable=AsyncMock, return_value=created):

        response = await anon_client.post("/api/auth/register", json={
            "email":    "newuser@finlit.test",
            "password": "secure123",
            "name":     "New User",
        })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@finlit.test"
    assert "hashed_password" not in data["user"]


# ─────────────────────────────────────────────────────────────────────────────
# 16. POST /api/auth/login — valid credentials return token
# ─────────────────────────────────────────────────────────────────────────────
async def test_login_user_returns_access_token_on_valid_credentials(anon_client):
    db_user = _make_db_user("alice@finlit.test", "correctpass")

    with patch("app.repositories.user_repo.find_user_by_email",
               new_callable=AsyncMock, return_value=db_user):

        response = await anon_client.post("/api/auth/login", json={
            "email":    "alice@finlit.test",
            "password": "correctpass",
        })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# ─────────────────────────────────────────────────────────────────────────────
# 17. GET /api/auth/me without Authorization header → 401
# ─────────────────────────────────────────────────────────────────────────────
async def test_protected_endpoint_returns_401_without_auth_token(anon_client):
    response = await anon_client.get("/api/auth/me")
    assert response.status_code == 401
