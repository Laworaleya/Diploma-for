from datetime import datetime, timezone, timedelta
from bson import ObjectId


def current_period() -> str:
    """Return current month as 'YYYY-MM'."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m")


def month_bounds() -> tuple[datetime, datetime]:
    """Return (start_of_month, now) in UTC."""
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now


def week_bounds() -> tuple[datetime, datetime]:
    """Return (7 days ago, now) in UTC."""
    now = datetime.now(timezone.utc)
    return now - timedelta(days=7), now


def today_bounds() -> tuple[datetime, datetime]:
    """Return (start_of_today, now) in UTC."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def fmt_amount(amount: float, currency: str = "₸") -> str:
    return f"{amount:,.0f} {currency}".replace(",", " ")


def serialize_doc(doc: dict) -> dict:
    if doc is None:
        return None
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    for k, v in list(result.items()):
        if isinstance(v, ObjectId):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
    return result
