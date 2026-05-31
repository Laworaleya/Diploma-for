import re
from typing import Dict, List, Tuple

from app.services.kaspi_import.amounts import AMOUNT_PATTERN, parse_amount


SUMMARY_START = "краткое содержание операций по карте"
TRANSACTION_TABLE_START = "дата сумма операция"


FIELD_SPECS = {
    "startBalance": {
        "label": r"Доступно\s+на\s+\d{2}[.]\d{2}[.]\d{2,4}",
        "warning": "Доступно на начало периода",
        "expense": False,
    },
    "topUps": {
        "label": r"Пополнения",
        "warning": "Пополнения",
        "expense": False,
    },
    "ownAccountIncome": {
        "label": r"Поступления\s+со\s+своих\s+счетов",
        "warning": "Поступления со своих счетов",
        "expense": False,
    },
    "transfers": {
        "label": r"Переводы(?!\s+на\s+свои\s+счета)",
        "warning": "Переводы",
        "expense": True,
    },
    "ownAccountTransfers": {
        "label": r"Переводы\s+на\s+свои\s+счета",
        "warning": "Переводы на свои счета",
        "expense": True,
    },
    "purchases": {
        "label": r"Покупки",
        "warning": "Покупки",
        "expense": True,
    },
    "cashWithdrawals": {
        "label": r"Снятия",
        "warning": "Снятия",
        "expense": True,
    },
    "other": {
        "label": r"Разное",
        "warning": "Разное",
        "expense": True,
    },
}


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_summary_block(text: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    lowered = text.lower()
    start = lowered.find(SUMMARY_START)
    if start == -1:
        warnings.append('Блок не найден: "Краткое содержание операций по карте"')
        return "", warnings

    end = lowered.find(TRANSACTION_TABLE_START, start)
    if end == -1:
        warnings.append('Не найдена граница таблицы операций после краткого содержания')
        return text[start:], warnings

    return text[start:end], warnings


def _extract_field(block: str, label_pattern: str) -> float | None:
    pattern = rf"(?:^|\s){label_pattern}\s*[:\-]?\s*({AMOUNT_PATTERN})\s*(?:₸|тг)?"
    match = re.search(pattern, block, flags=re.IGNORECASE)
    if not match:
        return None
    return parse_amount(match.group(1))


def parse_kaspi_summary(text: str) -> Tuple[Dict[str, float], List[str]]:
    summary = {key: 0.0 for key in FIELD_SPECS}
    warnings: List[str] = []
    block, block_warnings = extract_summary_block(text)
    warnings.extend(block_warnings)

    compact_block = _compact(block)
    if not compact_block:
        return summary, warnings

    for key, spec in FIELD_SPECS.items():
        value = _extract_field(compact_block, spec["label"])
        if value is None:
            warnings.append(f"Поле не найдено: {spec['warning']}")
            continue
        summary[key] = abs(value) if spec["expense"] else value

    return summary, warnings
