"""
END-TO-END TESTS — Real Kaspi Gold PDF (April 2026) through the full pipeline.

tests/fixtures/sample_kaspi.pdf  ← actual bank statement (4 pages, 95 transactions)

classify_merchants_with_ai is mocked to return {} so the test is:
  - deterministic (no live OpenAI call)
  - offline-friendly (no API key needed)
  - fast (no network round-trip)

All other stages (PDF extraction, transaction parsing, summary parsing,
chart building, category aggregation) run against REAL code and REAL PDF bytes.
That is what raises pdfParser.py and analyzer.py coverage.

Run:
    pytest tests/test_kaspi_pdf_e2e.py -v -s
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.services.kaspi_import.analyzer import analyze_kaspi_pdf

# ── Fixture PDF path ───────────────────────────────────────────────────────────
FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_kaspi.pdf"

# ── Ground-truth values confirmed by running the parser against the real PDF ──
# (verified: txn_expense_sum == summary_totalExpense exactly)
EXPECTED_TOTAL_INCOME  = 558562.66   # startBalance + topUps + ownAccountIncome
EXPECTED_TOTAL_EXPENSE = 522950.9    # transfers + ownAccountTransfers + purchases + other
EXPECTED_BALANCE_LEFT  = 35611.76    # matches "Доступно на 30.04.26" in the PDF
EXPECTED_TXN_COUNT     = 95          # all transaction rows on pages 2-4
EXPECTED_INCOME_TXNS   = 16          # positive-amount rows
EXPECTED_EXPENSE_TXNS  = 79          # negative-amount rows
EXPECTED_CHART_DAYS    = 30          # April has exactly 30 days
# When AI is off (merchant_categories={}), all "Покупка" transactions go to
# "Прочие расходы".  Verified from summary field "Покупки: 187 614,00 ₸".
EXPECTED_PURCHASES_SUM = 187614.0


@pytest.fixture(scope="module")
def pdf_bytes() -> bytes:
    assert FIXTURE_PDF.exists(), f"Fixture PDF not found: {FIXTURE_PDF}"
    return FIXTURE_PDF.read_bytes()


# AI mock reused in both tests — returns empty dict so no OpenAI call is made
_no_ai = patch(
    "app.services.kaspi_import.analyzer.classify_merchants_with_ai",
    new_callable=AsyncMock,
    return_value={},
)


# =============================================================================
# 1. Full pipeline: structure, period, totals, first transaction, chart length
# =============================================================================
async def test_real_kaspi_pdf_is_parsed_end_to_end(pdf_bytes):
    """
    Feeds real PDF bytes through analyze_kaspi_pdf() and checks that
    the result has the correct structure and matches the ground-truth numbers
    from the April 2026 Kaspi Gold statement.
    """
    with _no_ai:
        result = await analyze_kaspi_pdf(pdf_bytes)

    # ── Top-level keys ─────────────────────────────────────────────────────
    assert set(result.keys()) >= {
        "summary", "transactions", "chartData", "categories", "requiredCategories"
    }

    # ── Financial totals ───────────────────────────────────────────────────
    summary = result["summary"]
    assert summary["totalIncome"]  == pytest.approx(EXPECTED_TOTAL_INCOME,  abs=0.01)
    assert summary["totalExpense"] == pytest.approx(EXPECTED_TOTAL_EXPENSE, abs=0.01)
    assert summary["balanceLeft"]  == pytest.approx(EXPECTED_BALANCE_LEFT,  abs=0.01)

    # ── Transaction list ───────────────────────────────────────────────────
    txns = result["transactions"]
    assert len(txns) == EXPECTED_TXN_COUNT

    first = txns[0]
    assert first["date"]      == "2026-04-30"
    assert first["amount"]    == pytest.approx(-3153.0, abs=0.01)
    assert first["operation"] == "Покупка"
    assert first["details"]   == "Сердце столицы"

    # ── Chart covers all 30 days of April ──────────────────────────────────
    chart = result["chartData"]
    assert len(chart) == EXPECTED_CHART_DAYS
    assert chart[0]["date"]  == "2026-04-01"
    assert chart[-1]["date"] == "2026-04-30"

    # ── Categories (AI mocked → all purchases in "Прочие расходы") ─────────
    categories = result["categories"]
    assert isinstance(categories, list) and len(categories) > 0

    prochie = next(c for c in categories if c["name"] == "Прочие расходы")
    assert prochie["amount"] == pytest.approx(EXPECTED_PURCHASES_SUM, abs=0.01)

    assert result["requiredCategories"] == []


# =============================================================================
# 2. Transaction expense sum == summary totalExpense (to the tenge)
# =============================================================================
async def test_real_pdf_transaction_expense_sum_matches_summary_total(pdf_bytes):
    """
    Verifies the parser's internal consistency: summing all negative-amount
    transactions must equal the totalExpense figure from the summary block.
    This proves that the transaction parser and the summary parser extract
    the same financial data from the same PDF.
    """
    with _no_ai:
        result = await analyze_kaspi_pdf(pdf_bytes)

    transactions = result["transactions"]

    income_count  = sum(1 for t in transactions if t["amount"] > 0)
    expense_count = sum(1 for t in transactions if t["amount"] < 0)
    assert income_count  == EXPECTED_INCOME_TXNS
    assert expense_count == EXPECTED_EXPENSE_TXNS

    txn_expense_sum = round(
        sum(abs(t["amount"]) for t in transactions if t["amount"] < 0), 2
    )
    summary_total = result["summary"]["totalExpense"]

    assert txn_expense_sum == pytest.approx(summary_total, abs=0.01), (
        f"Transaction expense sum {txn_expense_sum} != summary totalExpense {summary_total}"
    )

    # Sum of "Покупка" transactions must equal the "Прочие расходы" category
    # amount when AI classification is disabled.
    purchases_sum = round(
        sum(
            abs(t["amount"])
            for t in transactions
            if t["amount"] < 0 and (t.get("operation") or "").lower() == "покупка"
        ),
        2,
    )
    assert purchases_sum == pytest.approx(EXPECTED_PURCHASES_SUM, abs=0.01)

    prochie = next(c for c in result["categories"] if c["name"] == "Прочие расходы")
    assert prochie["amount"] == pytest.approx(purchases_sum, abs=0.01)
