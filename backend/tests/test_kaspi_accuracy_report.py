"""
KASPI PARSER - Detalniy otchet tochnosti.

Zapusk:
    pytest tests/test_kaspi_accuracy_report.py -v -s

Kazhdiy test pechatat tablitsu 'ozhidanie vs fakt' s realnymi chislami.
"""

import sys

from app.services.kaspi_import.amounts import parse_amount
from app.services.kaspi_import.transactionParser import (
    extract_statement_period,
    parse_transactions,
)
from app.services.kaspi_import.kaspiSummaryParser import parse_kaspi_summary
from app.services.kaspi_import.financeCalculator import calculate_summary
from app.services.kaspi_import.categoryManager import (
    STANDARD_EXPENSE_CATEGORIES,
    build_categories_from_transactions,
)
from app.services.kaspi_import.chartDataBuilder import build_expense_chart_data


# Russian keywords MUST stay Russian — the parser regexes search for them.
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


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:,.2f}"
    return str(v)


def _check(label: str, actual, expected, results: list):
    ok = actual == expected
    results.append((label, expected, actual, ok))
    return ok


def _print(line: str = ""):
    """Write to stdout buffer directly, replacing unencodable chars."""
    enc = sys.stdout.encoding or "utf-8"
    sys.stdout.buffer.write(line.encode(enc, errors="replace") + b"\n")
    sys.stdout.buffer.flush()


# =============================================================================
def test_kaspi_parser_full_pipeline_accuracy_report():
    """
    Runs the complete Kaspi parser pipeline and prints a comparison table.
    Shows the commission real extracted values vs expected values.
    """
    period          = extract_statement_period(SAMPLE_KASPI_TEXT)
    transactions, _ = parse_transactions(SAMPLE_KASPI_TEXT)
    raw_summary, _  = parse_kaspi_summary(SAMPLE_KASPI_TEXT)
    calculated      = calculate_summary(raw_summary)
    chart           = build_expense_chart_data(transactions, period)
    categories      = build_categories_from_transactions(transactions, {})

    income_txns     = [t for t in transactions if t["amount"] > 0]
    expense_txns    = [t for t in transactions if t["amount"] < 0]
    txn_expense_sum = round(sum(abs(t["amount"]) for t in expense_txns), 2)
    chart_by_date   = {e["date"]: e["expense"] for e in chart}

    # "Prochie rashody" is the last standard category — fallback for AI-off
    last_std_cat = STANDARD_EXPENSE_CATEGORIES[-1]   # "Прочие расходы"
    prochie = next((c for c in categories if c["name"] == last_std_cat), None)

    results = []
    _check("Period start date",          period["startDate"],              "2025-05-01",  results)
    _check("Period end date",            period["endDate"],                "2025-05-31",  results)
    _check("Total transactions",         len(transactions),                7,              results)
    _check("Income transactions",        len(income_txns),                 1,              results)
    _check("Expense transactions",       len(expense_txns),                6,              results)
    _check("Sum of all expenses (KZT)",  txn_expense_sum,                  49850.0,        results)
    _check("Summary: topUps (KZT)",      raw_summary["topUps"],            150000.0,       results)
    _check("Summary: purchases (KZT)",   raw_summary["purchases"],         19850.0,        results)
    _check("Summary: transfers (KZT)",   raw_summary["transfers"],         20000.0,        results)
    _check("Summary: cashWithdrawals",   raw_summary["cashWithdrawals"],   10000.0,        results)
    _check("Calculated totalIncome",     calculated["totalIncome"],        155000.0,       results)
    _check("Calculated totalExpense",    calculated["totalExpense"],        49850.0,        results)
    _check("Calculated balanceLeft",     calculated["balanceLeft"],        105150.0,       results)
    _check("Chart days in period",       len(chart),                       31,             results)
    _check("Chart expense 01.05 (KZT)",  chart_by_date.get("2025-05-01"),  1500.0,         results)
    _check("Chart income day 05.05=0",   chart_by_date.get("2025-05-05"),  0.0,            results)
    _check("Chart expense 10.05 (KZT)",  chart_by_date.get("2025-05-10"),  20000.0,        results)
    _check("Category fallback (KZT)",    prochie["amount"] if prochie else None, 19850.0,  results)
    _check("parse_amount '12 500,00'",   parse_amount("12 500,00 ₸"), 12500.0,        results)
    _check("parse_amount '-850,00'",     parse_amount("-850,00"),           -850.0,         results)

    W = 72
    passed   = sum(1 for *_, ok in results if ok)
    total    = len(results)
    accuracy = passed / total * 100

    _print()
    _print("=" * W)
    _print("  KASPI PARSER ACCURACY REPORT")
    _print("=" * W)
    _print(f"  {'Check':<38} {'Expected':>12} {'Actual':>12}  {'':>4}")
    _print("-" * W)
    for label, expected, actual, ok in results:
        mark = "[OK]" if ok else "[FAIL] <=="
        _print(f"  {label:<38} {_fmt(expected):>12} {_fmt(actual):>12}  {mark}")
    _print("-" * W)
    _print(f"  Parser accuracy: {passed}/{total} checks = {accuracy:.0f}%")
    _print("=" * W)
    _print()

    assert passed == total, (
        f"Parser: {accuracy:.0f}% ({passed}/{total}). "
        f"Failed: {[r[0] for r in results if not r[3]]}"
    )


# =============================================================================
def test_amount_parser_format_table():
    """
    Prints a table of 8 real Kaspi amount formats vs parsed values.
    Shows the commission how the parser handles spaces, commas, and signs.
    """
    samples = [
        ("12 500,00 KZT",      "12 500,00 ₸",  12500.0),
        ("1 234 567,89",       "1 234 567,89",           1234567.89),
        ("-20 000,00 KZT",     "-20 000,00 ₸", -20000.0),
        ("-850,00",            "-850,00",                  -850.0),
        ("0,00 KZT",           "0,00 ₸",           0.0),
        ("150 000,00 tg",      "150 000,00 тг", 150000.0),
        ("5 000 (nbsp space)", "5\xa0000,00 ₸",  5000.0),
        ("None input",         None,                       0.0),
    ]

    W = 58
    passed = 0
    _print()
    _print("=" * W)
    _print("  KASPI AMOUNT PARSER - FORMAT TABLE")
    _print("=" * W)
    _print(f"  {'Format':<22} {'Expected':>12} {'Actual':>12}  {'':>4}")
    _print("-" * W)
    for display, raw, expected in samples:
        actual = parse_amount(raw)
        ok     = actual == expected
        if ok:
            passed += 1
        mark = "[OK]" if ok else "[FAIL] <=="
        _print(f"  {display:<22} {_fmt(expected):>12} {_fmt(actual):>12}  {mark}")
    _print("-" * W)
    _print(f"  Result: {passed}/{len(samples)} = {passed/len(samples)*100:.0f}%")
    _print("=" * W)
    _print()

    assert passed == len(samples)
