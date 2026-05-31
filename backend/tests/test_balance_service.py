"""
BALANCE SERVICE TESTS

Covers unaccounted_expense clamping, surplus calculation,
expense_ratio, and zero-income edge case.
"""

from app.services.balance_service import calculate_balance


# ─────────────────────────────────────────────────────────────────────────────
# 10. unaccounted_expense = max(0, total_expense - categorised_total)
# ─────────────────────────────────────────────────────────────────────────────
def test_balance_unaccounted_expense_is_zero_when_categories_cover_all_expenses():
    categories = [
        {"name": "Продукты",  "amount": 30000},
        {"name": "Транспорт", "amount": 15000},
        {"name": "Прочее",    "amount": 10000},
    ]
    result = calculate_balance(100000, 50000, categories)

    # categorised_total = 55 000 > total_expense 50 000 → clamp to 0
    assert result["unaccounted_expense"] == 0.0
    assert result["categorized_total"] == 55000.0


def test_balance_unaccounted_expense_equals_gap_when_categories_are_partial():
    categories = [
        {"name": "Продукты", "amount": 20000},
    ]
    result = calculate_balance(100000, 50000, categories)

    # 50 000 - 20 000 = 30 000 unaccounted
    assert result["unaccounted_expense"] == 30000.0


# ─────────────────────────────────────────────────────────────────────────────
# 11. surplus, expense_ratio, and zero-income edge case
# ─────────────────────────────────────────────────────────────────────────────
def test_balance_calculates_surplus_and_expense_ratio_correctly():
    categories = [{"name": "Еда", "amount": 75000}]
    result = calculate_balance(200000, 75000, categories)

    assert result["surplus"] == 125000.0
    assert result["expense_ratio"] == 37.5

    # category_breakdown should include "Еда" at 100%
    breakdown_names = [b["name"] for b in result["category_breakdown"]]
    assert "Еда" in breakdown_names
    eда_entry = next(b for b in result["category_breakdown"] if b["name"] == "Еда")
    assert eда_entry["percentage"] == 100.0


def test_balance_expense_ratio_is_zero_when_income_is_zero():
    result = calculate_balance(0, 10000, [{"name": "Расходы", "amount": 10000}])

    # Division by zero must not crash; ratio is 0
    assert result["expense_ratio"] == 0.0
    assert result["surplus"] == -10000.0
