"""
PARSER TESTS — Kaspi Bank PDF statement parser.

Covers amounts, period, summary block, transaction list, income/expense
sign logic, finance calculator totals, category fallback, garbage
resilience, and chart data aggregation.

Run:  pytest tests/test_kaspi_parser.py -v
"""

from app.services.kaspi_import.amounts import parse_amount
from app.services.kaspi_import.transactionParser import (
    extract_statement_period,
    parse_transactions,
)
from app.services.kaspi_import.kaspiSummaryParser import parse_kaspi_summary
from app.services.kaspi_import.financeCalculator import calculate_summary
from app.services.kaspi_import.categoryManager import build_categories_from_transactions
from app.services.kaspi_import.chartDataBuilder import build_expense_chart_data


# ── Synthetic Kaspi statement ──────────────────────────────────────────────────
#
# Numbers are internally consistent:
#   Purchases (Покупки) = 1 500 + 850 + 12 500 + 5 000 = 19 850 ₸
#   Transfers (Переводы)                                = 20 000 ₸
#   Cash withdrawals (Снятия)                          = 10 000 ₸
#   Total expense                                       = 49 850 ₸
#   Total income (Доступно + Пополнения)  = 5 000 + 150 000 = 155 000 ₸
#
SAMPLE_KASPI_TEXT = """\
Выписка по карте 4400 1234 5678 9000

за период с 01.05.2025 по 31.05.2025

Краткое содержание операций по карте

Доступно на 01.05.2025: 5 000,00 ₸
Пополнения: 150 000,00 ₸
Поступления со своих счетов: 0,00 ₸
Покупки: 19 850,00 ₸
Переводы: 20 000,00 ₸
Переводы на свои счета: 0,00 ₸
Снятия: 10 000,00 ₸
Разное: 0,00 ₸

Дата Сумма Операция
01.05.2025 -1 500,00 ₸ Покупка Магнум
03.05.2025 -850,00 ₸ Покупка Кофехауз
05.05.2025 150 000,00 ₸ Пополнение Зарплата ТОО Акмеон
10.05.2025 -20 000,00 ₸ Перевод Ахметов Арман
15.05.2025 -10 000,00 ₸ Снятие наличных ATM Алматы
20.05.2025 -12 500,00 ₸ Покупка Technodom
25.05.2025 -5 000,00 ₸ Покупка 2GIS Маркет
"""


# ─────────────────────────────────────────────────────────────────────────────
# 1. Amounts with spaces / commas / currency symbol parse to the correct float
# ─────────────────────────────────────────────────────────────────────────────
def test_parser_amounts_with_spaces_commas_and_currency_are_parsed_correctly():
    assert parse_amount("12 500,00 ₸") == 12500.0
    assert parse_amount("1 234 567,89") == 1234567.89
    assert parse_amount("-850,00") == -850.0
    assert parse_amount("0,00 ₸") == 0.0
    assert parse_amount("150 000,00 тг") == 150000.0
    assert parse_amount(None) == 0.0
    assert parse_amount("") == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Statement period is extracted as ISO date strings
# ─────────────────────────────────────────────────────────────────────────────
def test_parser_extracts_statement_period_as_iso_dates():
    period = extract_statement_period(SAMPLE_KASPI_TEXT)
    assert period is not None
    assert period["startDate"] == "2025-05-01"
    assert period["endDate"] == "2025-05-31"


def test_parser_returns_none_when_period_line_is_absent():
    assert extract_statement_period("Нет строки с периодом") is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Summary block: income and expense fields are extracted correctly
# ─────────────────────────────────────────────────────────────────────────────
def test_parser_summary_block_extracts_income_and_expense_fields():
    summary, warnings = parse_kaspi_summary(SAMPLE_KASPI_TEXT)

    assert summary["topUps"] == 150000.0
    assert summary["startBalance"] == 5000.0
    assert summary["ownAccountIncome"] == 0.0
    assert summary["purchases"] == 19850.0
    assert summary["transfers"] == 20000.0
    assert summary["cashWithdrawals"] == 10000.0
    assert summary["other"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 4. Transactions: correct count, date format, and amount value
# ─────────────────────────────────────────────────────────────────────────────
def test_parser_extracts_correct_transaction_count_date_and_amount():
    transactions, warnings = parse_transactions(SAMPLE_KASPI_TEXT)

    assert len(transactions) == 7

    first = transactions[0]
    assert first["date"] == "2025-05-01"
    assert first["amount"] == -1500.0
    assert first["operation"] == "Покупка"
    assert first["details"] == "Магнум"

    income_txn = transactions[2]
    assert income_txn["date"] == "2025-05-05"
    assert income_txn["amount"] == 150000.0
    assert income_txn["operation"] == "Пополнение"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Income (positive) and expenses (negative) are correctly distinguished
# ─────────────────────────────────────────────────────────────────────────────
def test_parser_correctly_separates_income_from_expenses_by_sign():
    transactions, _ = parse_transactions(SAMPLE_KASPI_TEXT)

    income = [t for t in transactions if t["amount"] > 0]
    expenses = [t for t in transactions if t["amount"] < 0]

    assert len(income) == 1
    assert income[0]["amount"] == 150000.0

    assert len(expenses) == 6
    expense_sum = sum(abs(t["amount"]) for t in expenses)
    assert expense_sum == 49850.0


# ─────────────────────────────────────────────────────────────────────────────
# 6. financeCalculator: totalExpense matches the sum of expense transactions
# ─────────────────────────────────────────────────────────────────────────────
def test_finance_calculator_total_expense_matches_transaction_sum():
    raw_summary, _ = parse_kaspi_summary(SAMPLE_KASPI_TEXT)
    calculated = calculate_summary(raw_summary)

    transactions, _ = parse_transactions(SAMPLE_KASPI_TEXT)
    txn_expense_sum = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)

    assert calculated["totalExpense"] == txn_expense_sum
    assert calculated["totalIncome"] == 155000.0


# ─────────────────────────────────────────────────────────────────────────────
# 7. categoryManager (AI off): expenses fall back to standard categories
# ─────────────────────────────────────────────────────────────────────────────
def test_category_manager_without_ai_assigns_expenses_to_prochie_rashody():
    purchase_transactions = [
        {"date": "2025-05-01", "amount": -1500.0,  "operation": "Покупка", "details": "Магнум"},
        {"date": "2025-05-03", "amount": -850.0,   "operation": "Покупка", "details": "Кофехауз"},
        {"date": "2025-05-20", "amount": -12500.0, "operation": "Покупка", "details": "Technodom"},
    ]

    # Empty merchant_categories simulates AI being disabled
    categories = build_categories_from_transactions(purchase_transactions, {})

    assert isinstance(categories, list)
    assert len(categories) > 0

    prochie = next((c for c in categories if c["name"] == "Прочие расходы"), None)
    assert prochie is not None
    assert prochie["amount"] == 14850.0  # 1500 + 850 + 12500


# ─────────────────────────────────────────────────────────────────────────────
# 8. Garbage / empty lines do not crash the parser
# ─────────────────────────────────────────────────────────────────────────────
def test_parser_handles_garbage_and_empty_lines_without_crashing():
    dirty_text = """\
Выписка по карте

за период с 01.06.2025 по 30.06.2025

Краткое содержание операций по карте
Пополнения: 50 000,00 ₸
Покупки: 5 000,00 ₸

Дата Сумма Операция
Lorem ipsum dolor sit amet
------------------------------
€€€ INVALID LINE
15.06.2025 -5 000,00 ₸ Покупка Магазин

   blank spaces everywhere
???no date here???
"""
    transactions, warnings = parse_transactions(dirty_text)

    assert isinstance(transactions, list)
    assert isinstance(warnings, list)
    # Only the valid transaction line should be parsed
    assert len(transactions) == 1
    assert transactions[0]["amount"] == -5000.0


# ─────────────────────────────────────────────────────────────────────────────
# 9. chartDataBuilder: daily expenses are aggregated correctly per date
# ─────────────────────────────────────────────────────────────────────────────
def test_chart_data_builder_aggregates_daily_expenses_by_date():
    transactions, _ = parse_transactions(SAMPLE_KASPI_TEXT)
    period = extract_statement_period(SAMPLE_KASPI_TEXT)

    chart_data = build_expense_chart_data(transactions, period)

    # Period is all of May 2025 → 31 daily entries
    assert len(chart_data) == 31

    by_date = {entry["date"]: entry["expense"] for entry in chart_data}

    assert by_date["2025-05-01"] == 1500.0
    assert by_date["2025-05-03"] == 850.0
    assert by_date["2025-05-05"] == 0.0    # income day — not an expense
    assert by_date["2025-05-10"] == 20000.0
    assert by_date["2025-05-15"] == 10000.0
    assert by_date["2025-05-20"] == 12500.0
    assert by_date["2025-05-25"] == 5000.0
