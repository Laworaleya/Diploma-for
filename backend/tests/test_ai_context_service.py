from app.services.ai_context_service import build_goal_context, build_report_context


def test_report_context_uses_safe_fields_and_explicit_empty_recurring_payments():
    report = {
        "id": "internal-report-id",
        "user_id": "internal-user-id",
        "period": "2026-05",
        "total_income": 500000,
        "total_expense": 320000,
        "unaccounted_expense": 25000,
        "surplus": 180000,
        "categories": [{"name": "Food", "amount": 90000, "custom": False}],
        "required_categories": [
            {
                "name": "Rent",
                "amount": 150000,
                "period": "monthly",
                "duration": "2026-12-31",
                "paymentDate": "2026-05-25",
            }
        ],
        "created_at": "2026-05-16T00:00:00Z",
    }

    context = build_report_context(report, [])
    data = context.model_dump()

    assert "id" not in data
    assert "user_id" not in data
    assert "created_at" not in data
    assert data["recurring_payments"] == []
    assert data["required_categories"][0]["name"] == "Rent"


def test_goal_context_includes_recent_reports_and_sanitized_recurring_payments():
    goal = {
        "id": "internal-goal-id",
        "user_id": "internal-user-id",
        "title": "Emergency fund",
        "goal_type": "savings",
        "target_amount": 1000000,
        "current_amount": 250000,
        "progress_percent": 25,
        "deadline": "2026-12-31",
        "description": "Safety cushion",
        "status": "active",
    }
    reports = [
        {
            "period": "2026-05",
            "total_income": 500000,
            "total_expense": 300000,
            "unaccounted_expense": 0,
            "surplus": 200000,
            "categories": [{"name": "Transport", "amount": 25000}],
        }
    ]
    payments = [
        {
            "id": "internal-payment-id",
            "user_id": "internal-user-id",
            "title": "Loan",
            "amount": 80000,
            "period": "monthly",
            "nextPaymentDate": "2026-05-20",
            "status": "soon",
            "source": "manual",
            "manualIconColor": "#fff",
        }
    ]

    context = build_goal_context(goal, reports, payments)
    data = context.model_dump()

    assert "id" not in data
    assert "user_id" not in data
    assert data["recent_reports"][0]["period"] == "2026-05"
    assert data["recurring_payments"][0] == {
        "title": "Loan",
        "amount": 80000.0,
        "period": "monthly",
        "nextPaymentDate": "2026-05-20",
        "status": "soon",
        "source": "manual",
    }
