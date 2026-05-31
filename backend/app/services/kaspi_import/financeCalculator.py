from typing import Dict, List


INCOME_KEYS = ("startBalance", "topUps", "ownAccountIncome")
EXPENSE_KEYS = (
    "transfers",
    "ownAccountTransfers",
    "purchases",
    "cashWithdrawals",
    "other",
)


def calculate_summary(summary: Dict[str, float]) -> Dict[str, float]:
    total_income = sum(float(summary.get(key, 0) or 0) for key in INCOME_KEYS)
    total_expense = sum(abs(float(summary.get(key, 0) or 0)) for key in EXPENSE_KEYS)
    balance_left = total_income - total_expense

    calculated = dict(summary)
    calculated["totalIncome"] = round(total_income, 2)
    calculated["totalExpense"] = round(total_expense, 2)
    calculated["balanceLeft"] = round(balance_left, 2)
    return calculated


def calculate_required_payment_total(required_categories: List[dict]) -> float:
    return round(sum(float(item.get("amount", 0) or 0) for item in required_categories), 2)


def calculate_money_after_required(balance_left: float, required_categories: List[dict]) -> float:
    return round(balance_left - calculate_required_payment_total(required_categories), 2)
