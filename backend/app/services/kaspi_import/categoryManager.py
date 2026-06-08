import asyncio
import json
import urllib.request
from typing import Dict, List

from app.config import settings
from app.core.cache import get_redis


STANDARD_EXPENSE_CATEGORIES = [
    "Продукты",
    "Кафе и рестораны",
    "Транспорт",
    "Такси",
    "Коммунальные услуги",
    "Связь и интернет",
    "Одежда и обувь",
    "Здоровье и аптека",
    "Развлечения",
    "Образование",
    "Погашение кредита",
    "Переводы людям",
    "Прочие расходы",
]

STANDARD_REQUIRED_CATEGORIES = [
    "Кредит",
    "Аренда",
    "Коммунальные платежи",
    "Подписки",
    "Учеба",
    "Связь",
]

_MERCHANT_CACHE_TTL = 30 * 24 * 3600  # 30 days


def get_default_categories() -> List[Dict[str, float | str]]:
    return [{"name": name, "amount": 0.0} for name in STANDARD_EXPENSE_CATEGORIES]


def sanitize_categories(categories: List[dict]) -> List[Dict[str, float | str]]:
    sanitized = []
    for category in categories:
        name = str(category.get("name", "")).strip()
        amount = max(0.0, float(category.get("amount", 0) or 0))
        if name:
            sanitized.append({"name": name, "amount": round(amount, 2)})
    return sanitized


def sanitize_required_categories(categories: List[dict]) -> List[dict]:
    sanitized = []
    for category in categories:
        name = str(category.get("name", "")).strip()
        if not name:
            continue

        item = {
            "name": name,
            "amount": round(max(0.0, float(category.get("amount", 0) or 0)), 2),
            "period": str(category.get("period", "")).strip() or "каждый месяц",
        }
        duration = str(category.get("duration", "")).strip()
        payment_date = str(category.get("paymentDate", "")).strip()
        if duration:
            item["duration"] = duration
        if payment_date:
            item["paymentDate"] = payment_date
        sanitized.append(item)
    return sanitized


def _make_tx_key(txn: dict) -> str:
    """Build 'Операция | Детали' label sent to AI for classification."""
    operation = (txn.get("operation") or "").strip()
    details = (txn.get("details") or "").strip()
    if operation and details:
        return f"{operation} | {details}"
    return details or operation


async def classify_merchants_with_ai(transactions: List[dict]) -> Dict[str, str]:
    """Return {tx_key: category_ru} for unique expense transactions.

    tx_key is 'Операция | Детали' (e.g. 'Покупка | MAGNUM').
    Checks Redis cache first; sends uncached entries to OpenAI in one batch.
    Skips classification silently if API key is missing or any call fails.
    """
    if not settings.OPENAI_API_KEY:
        return {}

    has_typed_purchases = any(
        (t.get("operation") or "").lower() == "покупка" for t in transactions
    )

    candidates: List[dict] = []
    for t in transactions:
        amount = float(t.get("amount", 0) or 0)
        if amount >= 0:
            continue
        operation = (t.get("operation") or "").lower()
        # If operations are typed, include all expense types except deposits/returns
        if has_typed_purchases and operation in ("пополнение", "поступление", "возврат"):
            continue
        if not has_typed_purchases and not t.get("details"):
            continue
        candidates.append(t)

    unique_keys = list({_make_tx_key(t) for t in candidates if _make_tx_key(t)})
    if not unique_keys:
        return {}

    result: Dict[str, str] = {}
    uncached: List[str] = []

    redis = get_redis()
    for key in unique_keys:
        cached_category = None
        if redis:
            try:
                cached_category = await redis.get(f"merchant_category:{key}")
            except Exception:
                pass
        if cached_category:
            result[key] = cached_category
        else:
            uncached.append(key)

    if uncached:
        ai_result = await _batch_classify_openai(uncached)
        for key, category in ai_result.items():
            result[key] = category
            if redis:
                try:
                    await redis.set(
                        f"merchant_category:{key}",
                        category,
                        ex=_MERCHANT_CACHE_TTL,
                    )
                except Exception:
                    pass

    return result


def build_categories_from_transactions(
    transactions: List[dict],
    merchant_categories: Dict[str, str],
) -> List[Dict[str, float | str]]:
    """Aggregate expense amounts by AI-classified category.

    Allows any category name returned by AI — not limited to STANDARD_EXPENSE_CATEGORIES.
    Categories with zero amount are omitted from the result.
    """
    totals: Dict[str, float] = {}

    has_typed_purchases = any(
        (t.get("operation") or "").lower() == "покупка" for t in transactions
    )

    for txn in transactions:
        amount = float(txn.get("amount", 0) or 0)
        if amount >= 0:
            continue
        operation = (txn.get("operation") or "").lower()
        if has_typed_purchases and operation in ("пополнение", "поступление", "возврат"):
            continue
        if not has_typed_purchases and not txn.get("details"):
            continue

        tx_key = _make_tx_key(txn)
        category = merchant_categories.get(tx_key, "Прочие расходы")
        totals[category] = totals.get(category, 0.0) + abs(amount)

    return [
        {"name": name, "amount": round(amount, 2)}
        for name, amount in sorted(totals.items(), key=lambda x: -x[1])
        if amount > 0
    ]


async def _batch_classify_openai(tx_keys: List[str]) -> Dict[str, str]:
    categories_list = "\n".join(f"- {cat}" for cat in STANDARD_EXPENSE_CATEGORIES)
    items_text = "\n".join(tx_keys)

    prompt = f"""Ты классификатор расходов по банковской выписке Kaspi.

Определи категорию для каждой операции. Используй ТОЛЬКО категории из списка:
{categories_list}

Правила:
1. Не ставь "Прочие расходы", если можно логично определить категорию.
2. "Прочие расходы" — только если операция реально непонятна.
3. Если тип операции "Перевод" — ставь "Переводы людям".
4. Если в деталях имя человека или фамилия с инициалом (например "IVANOV I.", "АХМЕТОВ А.") — это "Переводы людям".
5. Если есть "ИП" и название похоже на магазин/кафе/точку продаж — выбери наиболее вероятную категорию.

Формат входных данных: "ТипОперации | Детали".

Ответь ТОЛЬКО валидным JSON объектом формата {{"ТипОперации | Детали": "Категория"}}.

Операции:
{items_text}"""

    body = json.dumps(
        {
            "model": "gpt-5.4-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        raw = await asyncio.to_thread(_do_http_request, request)
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return {str(k): str(v) for k, v in parsed.items() if isinstance(v, str)}
    except Exception as exc:
        print(f"[MerchantClassifier] OpenAI error: {exc}")
        return {}


def _do_http_request(request: urllib.request.Request) -> str:
    with urllib.request.urlopen(request, timeout=30) as resp:
        return resp.read().decode("utf-8")
