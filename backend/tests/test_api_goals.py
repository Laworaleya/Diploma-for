"""
API GOALS TESTS

Covers goal creation and the automatic progress_percent enrichment
that the service layer adds on every goal response.
"""

from unittest.mock import AsyncMock, patch

from tests.conftest import FAKE_USER_ID


def _make_db_goal(current: float, target: float) -> dict:
    return {
        "id": "507f1f77bcf86cd799439030",
        "user_id": FAKE_USER_ID,
        "title": "Накопления на отпуск",
        "goal_type": "savings",
        "target_amount": target,
        "current_amount": current,
        "deadline": None,
        "status": "active",
        "description": None,
        "created_at": "2025-01-01T00:00:00",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 20. POST /api/goals — created goal has progress_percent in the response
# ─────────────────────────────────────────────────────────────────────────────
async def test_create_goal_returns_goal_with_progress_percent(user_client):
    db_goal = _make_db_goal(current=25000.0, target=100000.0)

    with patch("app.repositories.goal_repo.create_goal",
               new_callable=AsyncMock, return_value=db_goal):

        response = await user_client.post("/api/goals", json={
            "title":          "Накопления на отпуск",
            "goal_type":      "savings",
            "target_amount":  100000.0,
            "current_amount": 25000.0,
        })

    assert response.status_code == 200
    data = response.json()
    assert data["progress_percent"] == 25.0
    assert data["title"] == "Накопления на отпуск"


# ─────────────────────────────────────────────────────────────────────────────
# 21. progress_percent is capped at 100 when current exceeds target
# ─────────────────────────────────────────────────────────────────────────────
async def test_goal_progress_percent_is_capped_at_100_when_overfunded(user_client):
    db_goal = _make_db_goal(current=120000.0, target=100000.0)

    with patch("app.repositories.goal_repo.create_goal",
               new_callable=AsyncMock, return_value=db_goal):

        response = await user_client.post("/api/goals", json={
            "title":          "Overfunded goal",
            "goal_type":      "savings",
            "target_amount":  100000.0,
            "current_amount": 120000.0,
        })

    assert response.status_code == 200
    assert response.json()["progress_percent"] == 100.0
