from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.db import get_db
from bot.keyboards import MAIN_MENU
from bot.states import WAITING_BUDGET
from bot.utils import current_period, serialize_doc, fmt_amount


async def _get_or_create_user(telegram_id: int, first_name: str, username: str | None) -> dict:
    db = get_db()
    user = await db.users.find_one({"telegram_id": telegram_id})
    if user:
        return serialize_doc(user)

    from datetime import datetime, timezone
    doc = {
        "telegram_id": telegram_id,
        "telegram_username": username,
        "name": first_name,
        "preferred_language": "ru",
        "currency": "KZT",
        "role": "user",
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return doc


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    user = await _get_or_create_user(
        tg_user.id, tg_user.first_name, tg_user.username
    )
    context.user_data["user_id"] = user.get("id") or str(user.get("_id", ""))

    db = get_db()
    period = current_period()
    budget = await db.user_budgets.find_one({"user_id": context.user_data["user_id"], "period": period})

    if budget and budget.get("monthly_limit", 0) > 0:
        balance = budget.get("total_income", 0) - budget.get("total_expense", 0)
        await update.message.reply_text(
            f"👋 С возвращением, {tg_user.first_name}!\n\n"
            f"💰 Твой баланс: {fmt_amount(balance)}\n"
            f"🎯 Бюджет на месяц: {fmt_amount(budget['monthly_limit'])}",
            reply_markup=MAIN_MENU,
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"👋 Привет, {tg_user.first_name}! Добро пожаловать в FinLit.\n\n"
        "Я помогу тебе следить за расходами и бюджетом.\n\n"
        "💳 Для начала — какой у тебя месячный бюджет? Введи сумму в тенге:"
    )
    return WAITING_BUDGET


async def handle_budget_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "").replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введи корректную сумму, например: 150000")
        return WAITING_BUDGET

    db = get_db()
    user_id = context.user_data["user_id"]
    period = current_period()
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    await db.user_budgets.update_one(
        {"user_id": user_id, "period": period},
        {
            "$set": {"monthly_limit": amount, "updated_at": now},
            "$setOnInsert": {
                "total_income": amount,
                "total_expense": 0.0,
                "created_at": now,
            },
        },
        upsert=True,
    )

    await update.message.reply_text(
        f"✅ Бюджет установлен: {fmt_amount(amount)}\n\n"
        "Теперь можешь добавлять расходы и следить за балансом.",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END
