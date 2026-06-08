from telegram import Update
from telegram.ext import ContextTypes

from bot.db import get_db
from bot.keyboards import MAIN_MENU
from bot.utils import current_period, month_bounds, week_bounds, today_bounds, fmt_amount


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    user_id = context.user_data.get("user_id")
    period = current_period()

    budget = await db.user_budgets.find_one({"user_id": user_id, "period": period})
    if not budget:
        await update.message.reply_text(
            "📊 Данных пока нет. Добавь первый расход или доход.",
            reply_markup=MAIN_MENU,
        )
        return

    total_income = budget.get("total_income", 0)
    total_expense = budget.get("total_expense", 0)
    monthly_limit = budget.get("monthly_limit", 0)
    balance = total_income - total_expense

    msg = (
        f"💰 Баланс: {fmt_amount(balance)}\n"
    )
    if monthly_limit > 0:
        pct = int(total_expense / monthly_limit * 100)
        msg += f"🎯 Бюджет: {fmt_amount(total_expense)} / {fmt_amount(monthly_limit)} ({pct}%)\n"

    await update.message.reply_text(msg, reply_markup=MAIN_MENU)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    user_id = context.user_data.get("user_id")
    period = current_period()

    budget = await db.user_budgets.find_one({"user_id": user_id, "period": period})
    if not budget:
        await update.message.reply_text(
            "📊 Данных пока нет. Добавь первый расход или доход.",
            reply_markup=MAIN_MENU,
        )
        return

    total_income = budget.get("total_income", 0)
    total_expense = budget.get("total_expense", 0)
    monthly_limit = budget.get("monthly_limit", 0)
    balance = total_income - total_expense

    # Period totals
    today_start, now = today_bounds()
    week_start, _ = week_bounds()
    month_start, _ = month_bounds()

    async def expense_sum(since, until):
        pipeline = [
            {"$match": {"user_id": user_id, "type": "expense", "created_at": {"$gte": since, "$lte": until}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        async for doc in db.transactions.aggregate(pipeline):
            return doc["total"]
        return 0.0

    today_total = await expense_sum(today_start, now)
    week_total = await expense_sum(week_start, now)
    month_total = total_expense

    # Category breakdown
    cat_pipeline = [
        {"$match": {"user_id": user_id, "type": "expense", "created_at": {"$gte": month_start, "$lte": now}}},
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
        {"$sort": {"total": -1}},
        {"$limit": 5},
    ]
    categories = []
    async for doc in db.transactions.aggregate(cat_pipeline):
        categories.append((doc["_id"], doc["total"]))

    # Spending velocity and forecast
    days_passed = max((now - month_start).days, 1)
    daily_rate = month_total / days_passed if days_passed > 0 else 0
    days_left = int(balance / daily_rate) if daily_rate > 0 and balance > 0 else None

    month_name = now.strftime("%B %Y")
    lines = [f"📊 Статистика — {month_name}\n"]
    lines.append(f"💰 Баланс: {fmt_amount(balance)}")
    lines.append(f"📅 Сегодня: {fmt_amount(today_total)}")
    lines.append(f"📆 За неделю: {fmt_amount(week_total)}")
    lines.append(f"🗓 За месяц: {fmt_amount(month_total)}")

    if monthly_limit > 0:
        pct = int(month_total / monthly_limit * 100)
        lines.append(f"🎯 Бюджет: {fmt_amount(month_total)} / {fmt_amount(monthly_limit)} ({pct}%)")

    if categories:
        lines.append("\n📂 По категориям:")
        for cat, amt in categories:
            lines.append(f"  • {cat} — {fmt_amount(amt)}")

    lines.append(f"\n⚡ Скорость: ~{fmt_amount(daily_rate)}/день")
    if days_left is not None:
        lines.append(f"📆 Прогноз: хватит ещё на ~{days_left} дн.")
    else:
        lines.append("📆 Прогноз: данных недостаточно")

    await update.message.reply_text("\n".join(lines), reply_markup=MAIN_MENU)
