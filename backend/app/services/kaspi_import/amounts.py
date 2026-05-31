import re


AMOUNT_PATTERN = r"[+-]?\s*\d+(?:[\s\u00a0\u202f]\d{3})*(?:[,.]\d{2})?"


def parse_amount(value: str | None) -> float:
    if not value:
        return 0.0

    normalized = (
        value.replace("\u00a0", " ")
        .replace("\u202f", " ")
        .replace("₸", "")
        .replace("тг", "")
        .strip()
    )
    normalized = re.sub(r"\s+", "", normalized)
    normalized = normalized.replace(",", ".")
    normalized = re.sub(r"(?<=\d)\.(?=\d{3}(?:\.|$))", "", normalized)

    if normalized in {"", "+", "-"}:
        return 0.0

    try:
        return round(float(normalized), 2)
    except ValueError:
        return 0.0
