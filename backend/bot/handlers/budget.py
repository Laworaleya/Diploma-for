from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.db import get_db
from bot.keyboards import MAIN_MENU, settings_keyboard
from bot.states import ENTER_INCOME_AMOUNT, ENTER_NEW_BUDGET
from bot.utils import current_period, fmt_amount


async def start_add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Введи сумму дохода или пополнения:")
    return ENTER_INCOME_AMOUNT


async def handle_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "").replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введи корректную сумму, например: 50000")
        return ENTER_INCOME_AMOUNT

    db = get_db()
    user_id = context.user_data.get("user_id")
    period = current_period()
    now = datetime.now(timezone.utc)

    budget = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {
            "$inc": {"total_income": amount, "monthly_limit": amount},
            "$set": {"updated_at": now},
            "$setOnInsert": {"total_expense": 0.0, "created_at": now},
        },
        upsert=True,
        return_document=True,
    )

    # return_document=True returns the document AFTER the $inc update,
    # so total_income already includes the amount — don't add it again.
    total_income = budget.get("total_income", 0) if budget else amount
    total_expense = budget.get("total_expense", 0) if budget else 0
    balance = total_income - total_expense

    await update.message.reply_text(
        f"✅ Доход записан: {fmt_amount(amount)}\n"
        f"💰 Текущий баланс: {fmt_amount(balance)}",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    user_id = context.user_data.get("user_id")
    period = current_period()
    budget = await db.user_budgets.find_one({"user_id": user_id, "period": period})
    limit = budget.get("monthly_limit", 0) if budget else 0

    await update.message.reply_text(
        f"💳 Изменить бюджет\n\n💳 Текущий месячный бюджет: {fmt_amount(limit)}",
        reply_markup=settings_keyboard(),
    )


async def start_change_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💳 Введи новый месячный бюджет:")
    return ENTER_NEW_BUDGET


async def handle_new_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "").replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введи корректную сумму:")
        return ENTER_NEW_BUDGET

    db = get_db()
    user_id = context.user_data.get("user_id")
    period = current_period()
    now = datetime.now(timezone.utc)

    await db.user_budgets.update_one(
        {"user_id": user_id, "period": period},
        {
            "$set": {"monthly_limit": amount, "updated_at": now},
            "$setOnInsert": {"total_income": 0.0, "total_expense": 0.0, "created_at": now},
        },
        upsert=True,
    )

    await update.message.reply_text(
        f"✅ Бюджет обновлён: {fmt_amount(amount)}",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current flow and route menu-button presses to their real handlers."""
    from bot.handlers.stats import show_balance, show_stats
    from bot.handlers.expense import start_expense

    text = (update.message.text or "") if update.message else ""
    if text == "📊 Мой баланс":
        await show_balance(update, context)
    elif text == "📈 Статистика":
        await show_stats(update, context)
    elif text == "💳 Изменить бюджет":
        await show_settings(update, context)
    elif text == "➕ Добавить расход":
        await start_expense(update, context)
    else:
        await update.message.reply_text("❌ Отменено.", reply_markup=MAIN_MENU)
    return ConversationHandler.END
