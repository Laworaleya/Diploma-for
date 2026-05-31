"""
API ADMIN TESTS

Covers role-based access control:
  - regular user hitting an admin endpoint → 403
  - admin user hitting the same endpoint → 200
"""

from unittest.mock import AsyncMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# 24. Regular user receives 403 on admin endpoints
# ─────────────────────────────────────────────────────────────────────────────
async def test_regular_user_gets_403_on_admin_stats_endpoint(user_client):
    # user_client has role="user"; get_current_admin raises 403
    response = await user_client.get("/api/admin/stats")
    assert response.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# 25. Admin user can access admin stats
# ─────────────────────────────────────────────────────────────────────────────
async def test_admin_user_can_access_global_stats(admin_client):
    fake_stats = {
        "total_users": 42,
        "total_reports": 120,
        "total_goals": 67,
        "total_recurring_payments": 88,
    }

    with patch("app.repositories.admin_repo.get_global_stats",
               new_callable=AsyncMock, return_value=fake_stats):

        response = await admin_client.get("/api/admin/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 42
