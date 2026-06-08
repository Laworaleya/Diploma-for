import logging
import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot import db
from bot.states import (
    WAITING_BUDGET,
    SELECT_CATEGORY,
    CUSTOM_CATEGORY,
    ENTER_EXPENSE_AMOUNT,
    ENTER_INCOME_AMOUNT,
    ENTER_NEW_BUDGET,
)
from bot.handlers.start import cmd_start, handle_budget_input
from bot.handlers.expense import (
    start_expense,
    handle_category_choice,
    handle_custom_category,
    handle_expense_amount,
    cancel as expense_cancel,
)
from bot.handlers.budget import (
    start_add_income,
    handle_income_amount,
    show_settings,
    start_change_budget,
    handle_new_budget,
    cancel as budget_cancel,
)
from bot.handlers.stats import show_balance, show_stats
from bot.handlers.link import cmd_link
from bot.scheduler import register_jobs

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

_bot_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_bot_dir)
_project_dir = os.path.dirname(_backend_dir)
load_dotenv(os.path.join(_backend_dir, ".env"))
load_dotenv(os.path.join(_project_dir, ".env"))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Any main-menu button press should break out of an active conversation
_MENU_FILTER = filters.Regex(
    r"^(➕ Добавить расход|💰 Добавить доход|📊 Мой баланс|📈 Статистика|💳 Изменить бюджет)$"
)


async def _load_user_id(update: Update, context):
    """Middleware: ensure user_id is in user_data before any handler."""
    if "user_id" not in context.user_data:
        tg_user = update.effective_user
        if not tg_user:
            return
        database = db.get_db()
        user = await database.users.find_one({"telegram_id": tg_user.id})
        if user:
            context.user_data["user_id"] = str(user["_id"])


async def _error_handler(update: object, context) -> None:
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла ошибка. Попробуй ещё раз или нажми /start"
        )


def _register_handlers(app: Application) -> None:
    # ── /start onboarding ───────────────────────────────────────────────────
    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            WAITING_BUDGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_budget_input)
            ],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
        allow_reentry=True,
    )

    # ── Add expense ─────────────────────────────────────────────────────────
    expense_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Добавить расход$"), start_expense)
        ],
        states={
            SELECT_CATEGORY: [
                CallbackQueryHandler(handle_category_choice, pattern="^cat:"),
                # If user presses any menu button while choosing category — cancel
                MessageHandler(_MENU_FILTER, expense_cancel),
            ],
            CUSTOM_CATEGORY: [
                MessageHandler(_MENU_FILTER, expense_cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_category),
            ],
            ENTER_EXPENSE_AMOUNT: [
                MessageHandler(_MENU_FILTER, expense_cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense_amount),
            ],
        },
        fallbacks=[
            MessageHandler(_MENU_FILTER, expense_cancel),
            CommandHandler("cancel", expense_cancel),
        ],
        per_message=False,
        allow_reentry=True,
    )

    # ── Add income ──────────────────────────────────────────────────────────
    income_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💰 Добавить доход$"), start_add_income)
        ],
        states={
            ENTER_INCOME_AMOUNT: [
                MessageHandler(_MENU_FILTER, budget_cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income_amount),
            ],
        },
        fallbacks=[
            MessageHandler(_MENU_FILTER, budget_cancel),
            CommandHandler("cancel", budget_cancel),
        ],
        allow_reentry=True,
    )

    # ── Change budget ───────────────────────────────────────────────────────
    budget_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_change_budget, pattern="^settings:change_budget$")
        ],
        states={
            ENTER_NEW_BUDGET: [
                MessageHandler(_MENU_FILTER, budget_cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_budget),
            ],
        },
        fallbacks=[
            MessageHandler(_MENU_FILTER, budget_cancel),
            CommandHandler("cancel", budget_cancel),
        ],
        per_message=False,
        allow_reentry=True,
    )

    app.add_handler(start_conv)
    app.add_handler(expense_conv)
    app.add_handler(income_conv)
    app.add_handler(budget_conv)

    app.add_handler(CommandHandler("link", cmd_link))
    app.add_handler(MessageHandler(filters.Regex("^📊 Мой баланс$"), show_balance))
    app.add_handler(MessageHandler(filters.Regex("^📈 Статистика$"), show_stats))
    app.add_handler(MessageHandler(filters.Regex("^💳 Изменить бюджет$"), show_settings))

    # Runs before all other handlers to populate user_id in context
    app.add_handler(MessageHandler(filters.ALL, _load_user_id), group=-1)

    app.add_error_handler(_error_handler)


async def _post_init(_application: Application) -> None:
    await db.connect()
    logger.info("Connected to MongoDB")


async def _post_shutdown(_application: Application) -> None:
    await db.close()


def main() -> None:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    _register_handlers(app)
    register_jobs(app)

    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
