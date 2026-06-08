from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

EXPENSE_CATEGORIES = [
    "Обязательное",
    "Еда",
    "Транспорт",
    "Подписки",
    "Кредиты",
    "Одежда",
    "Развлечения",
    "Здоровье",
    "Другое",
]

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["➕ Добавить расход", "💰 Добавить доход"],
        ["📊 Мой баланс", "📈 Статистика"],
        ["💳 Изменить бюджет"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


def category_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(EXPENSE_CATEGORIES), 3):
        row = [
            InlineKeyboardButton(cat, callback_data=f"cat:{cat}")
            for cat in EXPENSE_CATEGORIES[i : i + 3]
        ]
        rows.append(row)
    rows.append([InlineKeyboardButton("✏️ Своя категория", callback_data="cat:__custom__")])
    return InlineKeyboardMarkup(rows)


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Изменить бюджет", callback_data="settings:change_budget")],
    ])
