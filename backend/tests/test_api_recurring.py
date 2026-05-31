"""
API RECURRING PAYMENTS TESTS

Covers creating a recurring payment (which derives next-date and status)
and listing payments (returns an empty list when none exist).
"""

from unittest.mock import AsyncMock, patch

from tests.conftest import FAKE_USER_ID

FAKE_PAYMENT = {
    "id": "507f1f77bcf86cd799439040",
    "user_id": FAKE_USER_ID,
    "title": "Аренда квартиры",
    "amount": 120000.0,
    "originalPaymentDate": "2020-01-10",
    "paymentDay": 10,
    "paymentMonth": 1,
    "paymentYear": 2020,
    "nextPaymentDate": "2026-06-10",
    "period": "monthly",
    "status": "safe",
    "iconColor": "green",
    "source": "manual",
}


# ─────────────────────────────────────────────────────────────────────────────
# 22. POST /api/recurring-payments — response has next date and valid status
# ─────────────────────────────────────────────────────────────────────────────
async def test_create_recurring_payment_returns_payment_with_next_date_and_status(user_client):
    with patch("app.repositories.recurring_payment_repo.find_duplicate",
               new_callable=AsyncMock, return_value=None), \
         patch("app.repositories.recurring_payment_repo.create_payment",
               new_callable=AsyncMock, return_value=FAKE_PAYMENT):

        response = await user_client.post("/api/recurring-payments", json={
            "title":               "Аренда квартиры",
            "amount":              120000.0,
            "originalPaymentDate": "10.01.2020",
            "period":              "monthly",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Аренда квартиры"
    assert data["status"] in ("safe", "soon", "urgent", "overdue")
    assert "nextPaymentDate" in data


# ─────────────────────────────────────────────────────────────────────────────
# 23. GET /api/recurring-payments — returns empty list when user has none
# ─────────────────────────────────────────────────────────────────────────────
async def test_list_recurring_payments_returns_empty_list_when_user_has_none(user_client):
    with patch("app.repositories.recurring_payment_repo.find_payments_by_user",
               new_callable=AsyncMock, return_value=[]):

        response = await user_client.get("/api/recurring-payments")

    assert response.status_code == 200
    assert response.json() == []
