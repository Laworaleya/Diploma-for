import calendar
from datetime import date, datetime
from typing import Literal
from uuid import uuid4


PaymentStatus = Literal["safe", "soon", "urgent", "overdue"]


STATUS_COLORS = {
    "safe": "green",
    "soon": "yellow",
    "urgent": "orange",
    "overdue": "red",
}


def parse_payment_date(value: str) -> date:
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError("Некорректная дата платежа")


def format_payment_date(value: date) -> str:
    return value.isoformat()


def _last_day(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _with_month(base: date, year: int, month: int) -> date:
    return date(year, month, min(base.day, _last_day(year, month)))


def _add_month(base: date) -> date:
    year = base.year + (1 if base.month == 12 else 0)
    month = 1 if base.month == 12 else base.month + 1
    return _with_month(base, year, month)


def calculateNextPaymentDate(paymentDate: str, period: str = "monthly") -> str:
    normalized_period = "monthly" if period in {"monthly", "каждый месяц"} else period
    if normalized_period != "monthly":
        raise ValueError("Поддерживается только периодичность monthly")

    original = parse_payment_date(paymentDate)
    today = date.today()
    candidate = _with_month(original, today.year, today.month)

    if candidate < today:
        candidate = _add_month(candidate)

    return format_payment_date(candidate)


def getDaysUntilPayment(nextPaymentDate: str) -> int:
    return (parse_payment_date(nextPaymentDate) - date.today()).days


def getPaymentStatus(daysUntil: int) -> PaymentStatus:
    if daysUntil <= 0:
        return "overdue"
    if daysUntil <= 3:
        return "urgent"
    if daysUntil <= 7:
        return "soon"
    return "safe"


def getIconColorByStatus(status: PaymentStatus) -> str:
    return STATUS_COLORS[status]


def build_recurring_payment_payload(
    *,
    title: str,
    amount: float,
    original_payment_date: str,
    period: str = "monthly",
    source: str = "manual",
    user_id: str | None = None,
    icon_color: str | None = None,
) -> dict:
    original = parse_payment_date(original_payment_date)
    next_payment_date = calculateNextPaymentDate(format_payment_date(original), period)
    days_until = getDaysUntilPayment(next_payment_date)
    status = getPaymentStatus(days_until)

    payload = {
        "title": title.strip(),
        "amount": round(float(amount), 2),
        "originalPaymentDate": format_payment_date(original),
        "paymentDay": original.day,
        "paymentMonth": original.month,
        "paymentYear": original.year,
        "nextPaymentDate": next_payment_date,
        "period": "monthly",
        "status": status,
        "iconColor": getIconColorByStatus(status),
        "source": source,
    }
    if user_id:
        payload["user_id"] = user_id
    if icon_color and source == "manual":
        payload["manualIconColor"] = icon_color
    return payload


def createRecurringPaymentFromRequiredCategory(category: dict) -> dict:
    payment_date = category.get("paymentDate") or category.get("duration")
    if not payment_date:
        raise ValueError("У обязательной категории не указана дата платежа")

    return build_recurring_payment_payload(
        title=category.get("name", ""),
        amount=category.get("amount", 0),
        original_payment_date=payment_date,
        period=category.get("period", "monthly"),
        source="requiredCategory",
    )


def make_payment_id() -> str:
    return str(uuid4())
