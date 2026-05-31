from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional


def _parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _range_days(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def build_expense_chart_data(
    transactions: List[dict],
    period: Optional[Dict[str, str]] = None,
) -> List[Dict[str, float | str]]:
    daily_expenses = defaultdict(float)

    for transaction in transactions:
        amount = float(transaction.get("amount", 0) or 0)
        if amount < 0:
            daily_expenses[transaction["date"]] += abs(amount)

    if period:
        start = _parse_iso_date(period["startDate"])
        end = _parse_iso_date(period["endDate"])
    elif transactions:
        parsed_dates = [_parse_iso_date(item["date"]) for item in transactions]
        start = min(parsed_dates)
        end = max(parsed_dates)
    else:
        return []

    return [
        {"date": day.isoformat(), "expense": round(daily_expenses[day.isoformat()], 2)}
        for day in _range_days(start, end)
    ]
