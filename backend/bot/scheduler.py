import datetime
import logging
from telegram.ext import Application

from bot.db import get_db
from bot.utils import fmt_amount

logger = logging.getLogger(__name__)


async def daily_expense_reminder(context):
    """Sends 'remember to log expenses' message to all users at 21:00 UTC."""
    db = get_db()
    cursor = db.users.find(
        {"telegram_id": {"$exists": True, "$ne": None}},
        {"telegram_id": 1},
    )
    async for user in cursor:
        try:
            await context.bot.send_message(
                chat_id=user["telegram_id"],
                text="📝 Не забудь записать расходы за сегодня!",
            )
        except Exception as e:
            logger.warning("Failed to send daily reminder to %s: %s", user["telegram_id"], e)


async def payment_reminders(context):
    """
    Sends payment reminders for recurring payments due in 3, 1 day or today.
    Runs daily at 09:00 UTC.
    """
    db = get_db()
    today = datetime.date.today()
    remind_offsets = {0: "🔴 Сегодня платёж", 1: "⚠️ Завтра платёж", 3: "⏰ Через 3 дня платёж"}

    for days_ahead, prefix in remind_offsets.items():
        target_date = today + datetime.timedelta(days=days_ahead)
        target_str = target_date.strftime("%Y-%m-%d")

        # recurring_payments stores nextPaymentDate as "YYYY-MM-DD" string
        from bson import ObjectId
        cursor = db.recurring_payments.find({"nextPaymentDate": target_str})
        async for payment in cursor:
            try:
                user = await db.users.find_one(
                    {"_id": ObjectId(payment["user_id"])},
                    {"telegram_id": 1},
                )
            except Exception:
                continue

            if not user or not user.get("telegram_id"):
                continue

            title = payment.get("title", "Платёж")
            amount = payment.get("amount", 0)
            try:
                await context.bot.send_message(
                    chat_id=user["telegram_id"],
                    text=f"{prefix}: {title} — {fmt_amount(amount)}",
                )
            except Exception as e:
                logger.warning("Failed to send payment reminder: %s", e)


def register_jobs(app: Application):
    jq = app.job_queue
    # Daily reminder at 21:00 UTC
    jq.run_daily(
        daily_expense_reminder,
        time=datetime.time(21, 0, 0, tzinfo=datetime.timezone.utc),
        name="daily_reminder",
    )
    # Payment reminders at 09:00 UTC
    jq.run_daily(
        payment_reminders,
        time=datetime.time(9, 0, 0, tzinfo=datetime.timezone.utc),
        name="payment_reminders",
    )
