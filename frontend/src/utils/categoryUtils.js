// Maps any stored category name (in any language) to its i18n key.
// Categories are stored as display strings, so we need reverse lookup on language switch.
const CATEGORY_KEY_MAP = {
  // ── Tracker predefined — Russian ────────────────────────────────────────────
  'Обязательное': 'tracker.categories.required',
  'Еда':          'tracker.categories.food',
  'Транспорт':    'tracker.categories.transport',
  'Подписки':     'tracker.categories.subscriptions',
  'Кредиты':      'tracker.categories.credits',
  'Одежда':       'tracker.categories.clothing',
  'Развлечения':  'tracker.categories.entertainment',
  'Здоровье':     'tracker.categories.health',
  'Другое':       'tracker.categories.other',
  // ── Tracker predefined — English ────────────────────────────────────────────
  'Required':      'tracker.categories.required',
  'Food':          'tracker.categories.food',
  'Transport':     'tracker.categories.transport',
  'Subscriptions': 'tracker.categories.subscriptions',
  'Credits':       'tracker.categories.credits',
  'Clothing':      'tracker.categories.clothing',
  'Entertainment': 'tracker.categories.entertainment',
  'Health':        'tracker.categories.health',
  'Other':         'tracker.categories.other',
  // ── Tracker predefined — Kazakh ─────────────────────────────────────────────
  'Міндетті':   'tracker.categories.required',
  'Тамақ':      'tracker.categories.food',
  'Көлік':      'tracker.categories.transport',
  'Жазылымдар': 'tracker.categories.subscriptions',
  'Несиелер':   'tracker.categories.credits',
  'Киім':       'tracker.categories.clothing',
  'Ойын-сауық': 'tracker.categories.entertainment',
  'Денсаулық':  'tracker.categories.health',
  'Басқа':      'tracker.categories.other',
  // ── Standard report categories (Kaspi) — Russian ────────────────────────────
  'Продукты':              'reports.categories_preset.food',
  'Питание':               'reports.categories_preset.food',
  'Кафе и рестораны':      'reports.categories_preset.restaurants',
  'Такси':                 'reports.categories_preset.taxi',
  'Коммунальные услуги':   'reports.categories_preset.utilities',
  'Коммунальные платежи':  'reports.categories_preset.utilities',
  'Связь и интернет':      'reports.categories_preset.communication',
  'Связь':                 'reports.categories_preset.communication',
  'Одежда и обувь':        'reports.categories_preset.clothing_shoes',
  'Здоровье и аптека':     'reports.categories_preset.health_pharmacy',
  'Образование':           'reports.categories_preset.education',
  'Учеба':                 'reports.categories_preset.education',
  'Погашение кредита':     'reports.categories_preset.loan',
  'Кредит':                'reports.categories_preset.loan',
  'Аренда':                'reports.categories_preset.rent',
  'Прочие расходы':        'reports.categories_preset.other_expenses',
  'Прочее':                'reports.categories_preset.other',
  'Прочие':                'reports.categories_preset.unaccounted',
  'Переводы людям':        'reports.categories_preset.transfers_people',
  // ── Standard report categories (Kaspi) — English ────────────────────────────
  'Groceries':            'reports.categories_preset.food',
  'Cafes & Restaurants':  'reports.categories_preset.restaurants',
  'Taxi':                 'reports.categories_preset.taxi',
  'Utilities':            'reports.categories_preset.utilities',
  'Internet & Phone':     'reports.categories_preset.communication',
  'Clothing & Footwear':  'reports.categories_preset.clothing_shoes',
  'Health & Pharmacy':    'reports.categories_preset.health_pharmacy',
  'Education':            'reports.categories_preset.education',
  'Loan Payment':         'reports.categories_preset.loan',
  'Rent':                 'reports.categories_preset.rent',
  'Other Expenses':       'reports.categories_preset.other_expenses',
  // ── Standard report categories (Kaspi) — Kazakh ─────────────────────────────
  'Тамақтану':                   'reports.categories_preset.food',
  'Кафелер мен мейрамханалар':   'reports.categories_preset.restaurants',
  'Коммуналдық қызметтер':       'reports.categories_preset.utilities',
  'Байланыс және интернет':      'reports.categories_preset.communication',
  'Киім мен аяқ киім':           'reports.categories_preset.clothing_shoes',
  'Денсаулық және дәріхана':     'reports.categories_preset.health_pharmacy',
  'Білім':                       'reports.categories_preset.education',
  'Несие өтеу':                  'reports.categories_preset.loan',
  'Жалдау':                      'reports.categories_preset.rent',
  'Басқа шығыстар':              'reports.categories_preset.other_expenses',
}

/**
 * Resolve a stored category name to the current locale's display string.
 * Falls back to the raw stored name if no mapping is found.
 */
export function resolveCategory(name, t) {
  if (!name) return name
  const key = CATEGORY_KEY_MAP[name]
  if (!key) return name
  const translated = t(key)
  // Vue I18n returns the key path if the key is missing — treat that as a miss
  return translated === key ? name : translated
}
