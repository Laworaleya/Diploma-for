import json
from typing import Optional

from fastapi import HTTPException

from app.models.ai_chat import AIChatCreate, AIContextSource
from app.repositories import admin_repo, ai_chat_repo
from app.services import goal_service, report_service, recurring_payment_service
from app.services.ai_context_service import build_goal_context, build_report_context
from app.services.openai_assistant_service import (
    OpenAIAssistantConfigError,
    OpenAIAssistantEmptyResponseError,
    OpenAIAssistantError,
    OpenAIAssistantTimeoutError,
    openai_assistant_service,
)


DEFAULT_CHAT_TITLE = "Новый AI-чат"


async def create_chat(user_id: str, data: AIChatCreate) -> dict:
    chat_data = {
        "user_id": user_id,
        "title": data.title or DEFAULT_CHAT_TITLE,
        "source": "manual",
        "source_label": None,
    }
    return _public_chat(await ai_chat_repo.create_chat(chat_data))


async def get_user_chats(user_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
    return await ai_chat_repo.find_chats_by_user(user_id, skip, limit)


async def get_chat_detail(chat_id: str, user_id: str) -> dict:
    chat = await _get_chat_or_404(chat_id, user_id)
    messages = await ai_chat_repo.find_messages_by_chat(chat_id, user_id)
    public_chat = _public_chat(chat)
    public_chat["messages"] = messages
    return public_chat


async def rename_chat(chat_id: str, user_id: str, title: str) -> dict:
    await _get_chat_or_404(chat_id, user_id)
    chat = await ai_chat_repo.update_chat(chat_id, user_id, {"title": title.strip()[:120]})
    if not chat:
        raise HTTPException(status_code=404, detail="AI chat not found")
    return _public_chat(chat)


async def delete_chat(chat_id: str, user_id: str) -> None:
    chat = await _get_chat_or_404(chat_id, user_id)
    await ai_chat_repo.delete_messages_by_chat(chat["id"])
    await ai_chat_repo.delete_chat(chat_id, user_id)


async def send_message(chat_id: str, user_id: str, content: str) -> dict:
    chat = await _get_chat_or_404(chat_id, user_id)
    if _should_generate_title(chat):
        chat = await ai_chat_repo.update_chat(
            chat_id,
            user_id,
            {"title": _generate_title(content), "source_label": "Обычный чат"},
        ) or chat
    return await _send_to_assistant(
        chat=chat,
        user_id=user_id,
        display_content=content.strip(),
        assistant_content=content.strip(),
        context_type="manual",
    )


async def analyze_report(report_id: str, current_user: dict) -> dict:
    user_id = current_user["id"]
    report = await report_service.get_report(report_id, user_id)
    recurring_payments = await recurring_payment_service.get_user_recurring_payments(user_id)
    context = build_report_context(report, recurring_payments)

    chat = await _create_context_chat(
        user_id=user_id,
        title=f"AI-анализ отчета {report['period']}",
        source="financial_report",
        source_label=f"Отчет {report['period']}",
    )
    display_content = f"Проанализируй финансовый отчет за {report['period']} с учетом регулярных платежей."
    assistant_content = _build_context_prompt(
        title="financial_report_analysis",
        language=current_user.get("preferred_language", "ru"),
        payload=context.model_dump(),
        task=(
            "Проанализируй отчет, учти все recurring_payments даже если список пуст, "
            "выдели риски, регулярную нагрузку, свободный остаток и 3-5 практичных шага."
        ),
    )
    return await _send_to_assistant(
        chat=chat,
        user_id=user_id,
        display_content=display_content,
        assistant_content=assistant_content,
        context_type="financial_report",
        tool_choice="required",
    )


async def plan_goal(goal_id: str, current_user: dict) -> dict:
    user_id = current_user["id"]
    goal = await goal_service.get_goal(goal_id, user_id)
    recent_reports = await report_service.get_user_reports(user_id, skip=0, limit=3)
    recurring_payments = await recurring_payment_service.get_user_recurring_payments(user_id)
    context = build_goal_context(goal, recent_reports, recurring_payments)

    chat = await _create_context_chat(
        user_id=user_id,
        title=f"AI-план: {goal['title']}",
        source="goal",
        source_label=goal["title"],
    )
    display_content = f"Составь план достижения цели: {goal['title']}."
    assistant_content = _build_context_prompt(
        title="goal_plan",
        language=current_user.get("preferred_language", "ru"),
        payload=context.model_dump(),
        task=(
            "Составь понятный план достижения цели: сколько нужно откладывать, "
            "какие расходы проверить, как учитывать регулярные платежи и что делать при отставании от срока."
        ),
    )
    return await _send_to_assistant(
        chat=chat,
        user_id=user_id,
        display_content=display_content,
        assistant_content=assistant_content,
        context_type="goal",
    )


async def analyze_tracker_report(period: str, current_user: dict) -> dict:
    """Build a tracker-based financial report and get AI analysis."""
    from calendar import monthrange
    from datetime import datetime, timezone
    from app.core.database import get_database

    user_id = current_user["id"]
    db = get_database()

    year, month = map(int, period.split("-"))
    month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day = monthrange(year, month)[1]
    month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    budget = await db.user_budgets.find_one({"user_id": user_id, "period": period})
    monthly_limit = budget.get("monthly_limit", 0) if budget else 0
    total_income = budget.get("total_income", 0) if budget else 0
    total_expense = budget.get("total_expense", 0) if budget else 0
    balance = total_income - total_expense
    usage_pct = round(total_expense / monthly_limit * 100, 1) if monthly_limit > 0 else 0

    cat_pipeline = [
        {"$match": {"user_id": user_id, "type": "expense", "created_at": {"$gte": month_start, "$lte": month_end}}},
        {"$group": {"_id": "$category", "amount": {"$sum": "$amount"}}},
        {"$sort": {"amount": -1}},
    ]
    categories = []
    async for doc in db.transactions.aggregate(cat_pipeline):
        pct = round(doc["amount"] / total_expense * 100, 1) if total_expense > 0 else 0
        categories.append({"name": doc["_id"], "amount": doc["amount"], "pct": pct})

    recurring_payments = await recurring_payment_service.get_user_recurring_payments(user_id)
    recurring_summary = [
        {
            "name": p.get("name"),
            "amount": p.get("amount"),
            "currency": p.get("currency"),
            "frequency": p.get("frequency"),
            "next_payment_date": str(p.get("nextPaymentDate", "")),
        }
        for p in recurring_payments
    ]

    month_names = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
    }
    month_label = f"{month_names.get(month, str(month))} {year}"

    payload = {
        "period": period,
        "month_label": month_label,
        "budget": {
            "monthly_limit": monthly_limit,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "usage_pct": usage_pct,
        },
        "categories": categories,
        "recurring_payments": recurring_summary,
    }

    display_content = f"Проанализируй мои расходы за {month_label} и дай финансовые советы."
    assistant_content = _build_context_prompt(
        title="tracker_report_analysis",
        language=current_user.get("preferred_language", "ru"),
        payload=payload,
        task=(
            "Проанализируй расходы из tracker-отчёта: оцени структуру трат, "
            "учти recurring_payments как обязательную нагрузку, "
            "выдели категории для экономии, дай 3-5 практичных советов и "
            "оцени финансовое здоровье по шкале 1-10 с объяснением."
        ),
    )

    chat = await _create_context_chat(
        user_id=user_id,
        title=f"AI-анализ трекера — {month_label}",
        source="financial_report",
        source_label=month_label,
    )
    return await _send_to_assistant(
        chat=chat,
        user_id=user_id,
        display_content=display_content,
        assistant_content=assistant_content,
        context_type="financial_report",
        tool_choice="required",
    )


async def _create_context_chat(
    user_id: str,
    title: str,
    source: AIContextSource,
    source_label: Optional[str],
) -> dict:
    return await ai_chat_repo.create_chat(
        {
            "user_id": user_id,
            "title": title[:120],
            "source": source,
            "source_label": source_label,
        }
    )


async def _send_to_assistant(
    chat: dict,
    user_id: str,
    display_content: str,
    assistant_content: str,
    context_type: AIContextSource,
    tool_choice: str | None = None,
) -> dict:
    # Load history before saving the new message so it isn't included
    history = await ai_chat_repo.find_messages_by_chat(chat["id"], user_id)

    user_message = await ai_chat_repo.create_message(
        {
            "chat_id": chat["id"],
            "user_id": user_id,
            "role": "user",
            "content": display_content,
            "context_type": context_type,
            "is_error": False,
        }
    )

    error = None
    try:
        answer = await openai_assistant_service.complete(history, assistant_content, tool_choice=tool_choice)
        assistant_message = await _create_assistant_message(chat["id"], user_id, answer, context_type)
    except OpenAIAssistantError as exc:
        error = _friendly_openai_error(exc)
        error_type = type(exc).__name__
        await admin_repo.log_ai_error(user_id, error_type, str(exc))
        assistant_message = await _create_assistant_message(
            chat["id"],
            user_id,
            error,
            context_type,
            is_error=True,
        )

    await ai_chat_repo.touch_chat(chat["id"], user_id)
    refreshed_chat = await ai_chat_repo.find_chat_by_id(chat["id"], user_id)
    return {
        "chat": _public_chat(refreshed_chat or chat),
        "user_message": _public_message(user_message),
        "assistant_message": _public_message(assistant_message),
        "error": error,
    }


async def _create_assistant_message(
    chat_id: str,
    user_id: str,
    content: str,
    context_type: AIContextSource,
    is_error: bool = False,
) -> dict:
    return await ai_chat_repo.create_message(
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "role": "assistant",
            "content": content,
            "context_type": context_type,
            "is_error": is_error,
        }
    )


async def _get_chat_or_404(chat_id: str, user_id: str) -> dict:
    chat = await ai_chat_repo.find_chat_by_id(chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="AI chat not found")
    return chat


def _build_context_prompt(title: str, language: str, payload: dict, task: str) -> str:
    context_json = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return (
        f"Ответь на языке: {language}.\n"
        f"Тип контекста: {title}.\n"
        f"Задача: {task}\n\n"
        "CONTEXT_JSON:\n"
        f"{context_json}"
    )


def _friendly_openai_error(exc: OpenAIAssistantError) -> str:
    if isinstance(exc, OpenAIAssistantConfigError):
        return "AI пока не настроен. Добавьте OPENAI_API_KEY на backend и повторите запрос."
    if isinstance(exc, OpenAIAssistantTimeoutError):
        return "AI не успел ответить вовремя. Попробуйте отправить сообщение еще раз."
    if isinstance(exc, OpenAIAssistantEmptyResponseError):
        return "AI вернул пустой ответ. Попробуйте переформулировать запрос."
    return f"Ошибка OpenAI: {exc}"


def _should_generate_title(chat: dict) -> bool:
    return chat.get("title") == DEFAULT_CHAT_TITLE and chat.get("source") == "manual"


def _generate_title(content: str) -> str:
    cleaned = " ".join(content.strip().split())
    if len(cleaned) <= 54:
        return cleaned or DEFAULT_CHAT_TITLE
    return f"{cleaned[:54].rstrip()}..."


def _public_chat(chat: dict) -> dict:
    public = dict(chat)
    public.pop("user_id", None)
    public.pop("openai_thread_id", None)
    return public


def _public_message(message: dict) -> dict:
    public = dict(message)
    public.pop("user_id", None)
    return public
