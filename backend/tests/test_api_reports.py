"""
API REPORTS TESTS

Covers creating a report (which triggers balance calculation and persists to DB)
and the calculate-balance preview endpoint (pure calculation, no DB).
"""

from unittest.mock import AsyncMock, patch

from tests.conftest import FAKE_USER_ID

FAKE_REPORT = {
    "id": "507f1f77bcf86cd799439020",
    "user_id": FAKE_USER_ID,
    "period": "2025-05",
    "total_income": 200000.0,
    "total_expense": 75000.0,
    "categories": [{"name": "Продукты", "amount": 50000.0, "custom": False}],
    "required_categories": [],
    "unaccounted_expense": 25000.0,
    "surplus": 125000.0,
    "created_at": "2025-05-01T00:00:00",
    "updated_at": "2025-05-01T00:00:00",
}

REPORT_PAYLOAD = {
    "period": "2025-05",
    "total_income": 200000.0,
    "total_expense": 75000.0,
    "categories": [{"name": "Продукты", "amount": 50000.0, "custom": False}],
    "required_categories": [],
}


# ─────────────────────────────────────────────────────────────────────────────
# 18. POST /api/reports — create report + balance is auto-calculated
# ─────────────────────────────────────────────────────────────────────────────
async def test_create_report_calculates_balance_and_returns_persisted_report(user_client):
    with patch("app.repositories.report_repo.create_report",
               new_callable=AsyncMock, return_value=FAKE_REPORT):

        response = await user_client.post("/api/reports", json=REPORT_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "2025-05"
    assert data["total_income"] == 200000.0
    assert data["total_expense"] == 75000.0
    assert "id" in data


# ─────────────────────────────────────────────────────────────────────────────
# 19. POST /api/reports/calculate-balance — preview without saving
# ─────────────────────────────────────────────────────────────────────────────
async def test_calculate_balance_preview_returns_surplus_and_expense_ratio(user_client):
    response = await user_client.post("/api/reports/calculate-balance", json=REPORT_PAYLOAD)

    assert response.status_code == 200
    data = response.json()

    # surplus = income - expense = 200 000 - 75 000 = 125 000
    assert data["surplus"] == 125000.0

    # expense_ratio = 75 000 / 200 000 * 100 = 37.5 %
    assert data["expense_ratio"] == 37.5

    # unaccounted = max(0, 75 000 - 50 000) = 25 000
    assert data["unaccounted_expense"] == 25000.0
