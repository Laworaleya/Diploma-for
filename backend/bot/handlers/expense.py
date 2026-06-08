from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.db import get_db
from bot.keyboards import MAIN_MENU, category_keyboard
from bot.states import SELECT_CATEGORY, CUSTOM_CATEGORY, ENTER_EXPENSE_AMOUNT
from bot.utils import current_period, fmt_amount


async def start_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📂 Выбери категорию расхода:",
        reply_markup=category_keyboard(),
    )
    return SELECT_CATEGORY


async def handle_category_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # "cat:Еда" or "cat:__custom__"
    category = data.split(":", 1)[1]

    if category == "__custom__":
        await query.edit_message_text("✏️ Введи название своей категории:")
        return CUSTOM_CATEGORY

    context.user_data["expense_category"] = category
    await query.edit_message_text(f"📂 Категория: {category}\n\n💸 Введи сумму расхода:")
    return ENTER_EXPENSE_AMOUNT


async def handle_custom_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text.strip()
    if not category:
        await update.message.reply_text("❌ Введи название категории:")
        return CUSTOM_CATEGORY

    context.user_data["expense_category"] = category
    await update.message.reply_text(f"📂 Категория: {category}\n\n💸 Введи сумму расхода:")
    return ENTER_EXPENSE_AMOUNT


async def handle_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "").replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введи корректную сумму, например: 2500")
        return ENTER_EXPENSE_AMOUNT

    db = get_db()
    user_id = context.user_data.get("user_id")
    category = context.user_data.get("expense_category", "Другое")
    period = current_period()
    now = datetime.now(timezone.utc)

    # Save transaction
    await db.transactions.insert_one({
        "user_id": user_id,
        "type": "expense",
        "amount": amount,
        "category": category,
        "description": None,
        "created_at": now,
    })

    # Update budget
    budget = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {
            "$inc": {"total_expense": amount},
            "$set": {"updated_at": now},
            "$setOnInsert": {"monthly_limit": 0.0, "total_income": 0.0, "created_at": now},
        },
        upsert=True,
        return_document=True,
    )

    # return_document=True returns the document AFTER the $inc update,
    # so total_expense already includes the amount — don't add it again.
    monthly_limit = budget.get("monthly_limit", 0) if budget else 0
    total_income = budget.get("total_income", 0) if budget else 0
    total_expense = budget.get("total_expense", 0) if budget else amount
    balance = total_income - total_expense

    usage_pct = int((total_expense / monthly_limit * 100)) if monthly_limit > 0 else 0

    summary = (
        f"✅ Расход записан\n\n"
        f"💸 Сумма: {fmt_amount(amount)}\n"
        f"📂 Категория: {category}\n"
        f"💰 Текущий баланс: {fmt_amount(balance)}\n"
    )
    if monthly_limit > 0:
        summary += f"📊 Использовано: {usage_pct}% бюджета ({fmt_amount(total_expense)} / {fmt_amount(monthly_limit)})"

    await update.message.reply_text(summary, reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current flow and route menu-button presses to their real handlers."""
    from bot.handlers.stats import show_balance, show_stats
    from bot.handlers.budget import show_settings, start_add_income

    text = (update.message.text or "") if update.message else ""
    if text == "📊 Мой баланс":
        await show_balance(update, context)
    elif text == "📈 Статистика":
        await show_stats(update, context)
    elif text == "💳 Изменить бюджет":
        await show_settings(update, context)
    elif text == "💰 Добавить доход":
        await start_add_income(update, context)
    else:
        await update.message.reply_text("❌ Отменено.", reply_markup=MAIN_MENU)
    return ConversationHandler.END
