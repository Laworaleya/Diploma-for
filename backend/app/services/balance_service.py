from typing import List


def calculate_balance(
    total_income: float,
    total_expense: float,
    categories: List[dict],
) -> dict:
    """
    Core balancing algorithm.

    Calculates:
    - categorized_total: sum of all explicitly named categories
    - unaccounted_expense: total_expense - categorized_total (transfers, cash, etc.)
    - surplus: total_income - total_expense (free money)
    - expense_ratio: what percentage of income is spent
    - category_breakdown: per-category percentage of total_expense
    """
    categorized_total = sum(cat.get("amount", 0) for cat in categories)
    unaccounted_expense = max(0, total_expense - categorized_total)
    surplus = total_income - total_expense
    expense_ratio = (total_expense / total_income * 100) if total_income > 0 else 0

    # Build category breakdown with percentages
    category_breakdown = []
    for cat in categories:
        amount = cat.get("amount", 0)
        percentage = (amount / total_expense * 100) if total_expense > 0 else 0
        category_breakdown.append({
            "name": cat["name"],
            "amount": amount,
            "percentage": round(percentage, 1),
            "custom": cat.get("custom", False),
        })

    # Add unaccounted as a virtual category
    if unaccounted_expense > 0:
        unaccounted_pct = (
            (unaccounted_expense / total_expense * 100) if total_expense > 0 else 0
        )
        category_breakdown.append({
            "name": "other",
            "amount": round(unaccounted_expense, 2),
            "percentage": round(unaccounted_pct, 1),
            "custom": False,
        })

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "categorized_total": round(categorized_total, 2),
        "unaccounted_expense": round(unaccounted_expense, 2),
        "surplus": round(surplus, 2),
        "expense_ratio": round(expense_ratio, 1),
        "category_breakdown": category_breakdown,
    }
