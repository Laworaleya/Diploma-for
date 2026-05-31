import re
from datetime import date
from typing import Dict, List, Optional, Tuple

from app.services.kaspi_import.amounts import AMOUNT_PATTERN, parse_amount


DATE_PATTERN = r"\d{2}[.]\d{2}[.]\d{2,4}"
TRANSACTION_RE = re.compile(
    rf"^\s*(?P<date>{DATE_PATTERN})\s+(?P<amount>{AMOUNT_PATTERN})\s*(?:₸|тг)?\s*(?P<tail>.+)?$",
    re.IGNORECASE,
)
PERIOD_RE = re.compile(
    rf"за\s+период\s+с\s+(?P<start>{DATE_PATTERN})\s+по\s+(?P<end>{DATE_PATTERN})",
    re.IGNORECASE,
)

# Sorted longest-first so regex alternation matches longer phrases before shorter ones
_KNOWN_OPERATIONS = sorted(
    [
        "Поступление со своего счета",
        "Снятие наличных",
        "Перевод с карты",
        "Покупка",
        "Пополнение",
        "Поступление",
        "Перевод",
        "Возврат",
        "Оплата",
    ],
    key=len,
    reverse=True,
)
_OPERATION_RE = re.compile(
    r"^(?P<operation>" + "|".join(re.escape(op) for op in _KNOWN_OPERATIONS) + r")\s*(?P<details>.+)?$",
    re.IGNORECASE,
)


def parse_kaspi_date(value: str) -> date:
    day, month, year = value.split(".")
    if len(year) == 2:
        year = f"20{year}"
    return date(int(year), int(month), int(day))


def format_date(value: date) -> str:
    return value.isoformat()


def extract_statement_period(text: str) -> Optional[Dict[str, str]]:
    match = PERIOD_RE.search(text)
    if not match:
        return None
    return {
        "startDate": format_date(parse_kaspi_date(match.group("start"))),
        "endDate": format_date(parse_kaspi_date(match.group("end"))),
    }


def _parse_tail(tail: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not tail:
        return None, None
    tail = tail.strip()
    if not tail:
        return None, None
    m = _OPERATION_RE.match(tail)
    if m:
        operation = m.group("operation").strip() or None
        details = (m.group("details") or "").strip() or None
        return operation, details
    return None, tail


def parse_transactions(text: str) -> Tuple[List[Dict], List[str]]:
    transactions: List[Dict] = []
    warnings: List[str] = []

    for line in text.splitlines():
        match = TRANSACTION_RE.match(line)
        if not match:
            continue

        try:
            parsed_date = parse_kaspi_date(match.group("date"))
        except ValueError:
            warnings.append(f"Некорректная дата операции: {match.group('date')}")
            continue

        operation, details = _parse_tail(match.group("tail"))
        transactions.append({
            "date": format_date(parsed_date),
            "amount": parse_amount(match.group("amount")),
            "operation": operation,
            "details": details,
        })

    if not transactions:
        warnings.append("Операции не найдены")

    return transactions, warnings
