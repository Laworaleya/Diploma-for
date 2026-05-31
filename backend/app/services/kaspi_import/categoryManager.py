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


async def classify_merchants_with_ai(transactions: List[dict]) -> Dict[str, str]:
    """Return {merchant: category_ru} for unique 'Покупка' merchants.

    Checks Redis cache first (key merchant_category:{name}, TTL 30 days).
    Sends uncached merchants to OpenAI gpt-4o-mini in a single batch request.
    Skips classification silently if API key is missing or Redis/OpenAI fails.
    """
    if not settings.OPENAI_API_KEY:
        return {}

    # Primary: transactions explicitly tagged as "Покупка"
    merchants = list({
        t["details"]
        for t in transactions
        if (t.get("operation") or "").lower() == "покупка" and t.get("details")
    })
    # Fallback: if PDF extraction put operation on a separate line, operation is None
    # In that case classify all negative-amount transactions that have a details field
    if not merchants:
        merchants = list({
            t["details"]
            for t in transactions
            if not t.get("operation") and t.get("details") and float(t.get("amount", 0) or 0) < 0
        })
    if not merchants:
        return {}

    result: Dict[str, str] = {}
    uncached: List[str] = []

    redis = get_redis()
    for merchant in merchants:
        cached_category = None
        if redis:
            try:
                cached_category = await redis.get(f"merchant_category:{merchant}")
            except Exception:
                pass
        if cached_category:
            result[merchant] = cached_category
        else:
            uncached.append(merchant)

    if uncached:
        ai_result = await _batch_classify_openai(uncached)
        for merchant, category in ai_result.items():
            result[merchant] = category
            if redis:
                try:
                    await redis.set(
                        f"merchant_category:{merchant}",
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
    """Aggregate 'Покупка' expense amounts by AI-classified category."""
    valid_categories = set(STANDARD_EXPENSE_CATEGORIES)
    totals: Dict[str, float] = {name: 0.0 for name in STANDARD_EXPENSE_CATEGORIES}

    has_typed_purchases = any(
        (t.get("operation") or "").lower() == "покупка" for t in transactions
    )
    for txn in transactions:
        operation = (txn.get("operation") or "").lower()
        amount = float(txn.get("amount", 0) or 0)
        if amount >= 0:
            continue
        # If operations are typed, only aggregate "Покупка"; otherwise aggregate all expenses with details
        if has_typed_purchases and operation != "покупка":
            continue
        if not has_typed_purchases and not txn.get("details"):
            continue
        merchant = txn.get("details") or ""
        category = merchant_categories.get(merchant, "Прочие расходы")
        if category not in valid_categories:
            category = "Прочие расходы"
        totals[category] += abs(amount)

    return [
        {"name": name, "amount": round(totals[name], 2)}
        for name in STANDARD_EXPENSE_CATEGORIES
    ]


async def _batch_classify_openai(merchants: List[str]) -> Dict[str, str]:
    categories_list = "\n".join(f"- {cat}" for cat in STANDARD_EXPENSE_CATEGORIES)
    prompt = (
        "Определи категорию трат для каждого мерчанта из списка. "
        "Используй ТОЛЬКО категории из списка ниже. "
        "Если не можешь определить — используй \"Прочие расходы\". "
        "Ответь ТОЛЬКО валидным JSON объектом формата {\"Merchant\": \"Категория\"}.\n\n"
        f"Допустимые категории:\n{categories_list}\n\n"
        "Мерчанты:\n" + "\n".join(merchants)
    )

    body = json.dumps(
        {
            "model": "gpt-4o-mini",
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
