"""
Shared fixtures for the FinLit test suite.

All API tests use httpx.AsyncClient with ASGITransport (no live network).
MongoDB startup is patched out so no running Mongo is required.
Redis is already optional (get_redis returns None when REDIS_URI is unset).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.dependencies import get_current_user, get_current_admin

# ── Fixed test identities ──────────────────────────────────────────────────────
FAKE_USER_ID = "507f1f77bcf86cd799439011"
FAKE_ADMIN_ID = "507f1f77bcf86cd799439012"

FAKE_USER = {
    "id": FAKE_USER_ID,
    "email": "testuser@finlit.test",
    "name": "Тест Пользователь",
    "role": "user",
    "preferred_language": "ru",
    "currency": "KZT",
    "created_at": "2025-01-01T00:00:00",
}

FAKE_ADMIN = {
    "id": FAKE_ADMIN_ID,
    "email": "admin@finlit.test",
    "name": "Администратор",
    "role": "admin",
    "preferred_language": "ru",
    "currency": "KZT",
    "created_at": "2025-01-01T00:00:00",
}


# ── Prevent real MongoDB/cache connections in every test ──────────────────────
@pytest.fixture(autouse=True)
def _mock_db_connections():
    """
    Patch connect_db / close_db in app.main so the ASGI lifespan never tries
    to reach a real MongoDB instance.  Also sets _database to a MagicMock so
    that any unpatched get_database() call doesn't crash with AttributeError.
    """
    import app.core.database as _db_mod

    with patch("app.main.connect_db", new_callable=AsyncMock), \
         patch("app.main.close_db", new_callable=AsyncMock):
        original = _db_mod._database
        _db_mod._database = MagicMock()
        yield
        _db_mod._database = original


# ── Convenience dict fixtures ──────────────────────────────────────────────────
@pytest.fixture
def fake_user():
    return FAKE_USER.copy()


@pytest.fixture
def fake_admin():
    return FAKE_ADMIN.copy()


# ── HTTP client fixtures ───────────────────────────────────────────────────────
@pytest.fixture
async def anon_client():
    """Unauthenticated client – used to verify that protected routes reject it."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def user_client():
    """Authenticated as a regular user; bypasses JWT + DB lookup."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def admin_client():
    """Authenticated as admin; overrides both get_current_user and get_current_admin."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_ADMIN
    app.dependency_overrides[get_current_admin] = lambda: FAKE_ADMIN
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_current_admin, None)
