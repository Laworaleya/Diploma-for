from bson import ObjectId
from telegram import Update
from telegram.ext import ContextTypes

from bot.db import get_db
from bot.keyboards import MAIN_MENU


async def cmd_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /link CODE — links the Telegram account to an existing web account.
    Migrates all transactions and budgets to the web user, then removes
    the standalone bot-created user.
    """
    if not context.args:
        await update.message.reply_text(
            "Использование: /link КОД\n\n"
            "Получи код на странице Трекера на сайте FinLit."
        )
        return

    code = context.args[0].strip()
    db = get_db()
    tg_user = update.effective_user

    # 1. Find the link code document
    link_doc = await db.link_codes.find_one({"code": code})
    if not link_doc:
        await update.message.reply_text(
            "❌ Код неверный или истёк (действует 10 минут).\n"
            "Запроси новый код на странице Трекера."
        )
        return

    web_user_id = link_doc["user_id"]

    # 2. Check web user exists
    try:
        web_user = await db.users.find_one({"_id": ObjectId(web_user_id)})
    except Exception:
        web_user = None
    if not web_user:
        await update.message.reply_text("❌ Аккаунт не найден. Попробуй войти на сайт заново.")
        return

    # 3. Find the current bot user (by telegram_id)
    bot_user = await db.users.find_one({"telegram_id": tg_user.id})
    bot_user_id = str(bot_user["_id"]) if bot_user else None

    # 4. If there's a separate bot user — migrate its data to the web user
    if bot_user_id and bot_user_id != web_user_id:
        # Migrate transactions
        await db.transactions.update_many(
            {"user_id": bot_user_id},
            {"$set": {"user_id": web_user_id}},
        )

        # Migrate budgets (period by period)
        async for bot_budget in db.user_budgets.find({"user_id": bot_user_id}):
            period = bot_budget["period"]
            existing = await db.user_budgets.find_one({"user_id": web_user_id, "period": period})
            if existing:
                # Overwrite with bot data (bot data is the real Telegram activity)
                await db.user_budgets.update_one(
                    {"user_id": web_user_id, "period": period},
                    {"$set": {
                        "monthly_limit": bot_budget.get("monthly_limit", 0),
                        "total_income":  bot_budget.get("total_income", 0),
                        "total_expense": bot_budget.get("total_expense", 0),
                        "updated_at":    bot_budget.get("updated_at"),
                    }},
                )
            else:
                bot_budget["user_id"] = web_user_id
                bot_budget.pop("_id", None)
                await db.user_budgets.insert_one(bot_budget)

        # Remove bot user's now-migrated budgets and the bot user itself
        await db.user_budgets.delete_many({"user_id": bot_user_id})
        await db.users.delete_one({"_id": bot_user["_id"]})

    # 5. Set telegram_id on the web user
    await db.users.update_one(
        {"_id": ObjectId(web_user_id)},
        {"$set": {
            "telegram_id": tg_user.id,
            "telegram_username": tg_user.username,
        }},
    )

    # 6. Update context so subsequent bot actions use the web user's id
    context.user_data["user_id"] = web_user_id

    # 7. Delete the used code
    await db.link_codes.delete_one({"code": code})

    await update.message.reply_text(
        f"✅ Аккаунты успешно привязаны!\n\n"
        f"Теперь все данные из бота синхронизированы с сайтом.\n"
        f"Открой страницу Трекера — там появятся твои расходы.",
        reply_markup=MAIN_MENU,
    )
