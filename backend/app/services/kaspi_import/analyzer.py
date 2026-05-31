from typing import Dict, List

from app.services.kaspi_import.categoryManager import (
    build_categories_from_transactions,
    classify_merchants_with_ai,
    get_default_categories,
)
from app.services.kaspi_import.chartDataBuilder import build_expense_chart_data
from app.services.kaspi_import.financeCalculator import calculate_summary
from app.services.kaspi_import.kaspiSummaryParser import parse_kaspi_summary
from app.services.kaspi_import.pdfParser import extract_text_from_pdf
from app.services.kaspi_import.transactionParser import (
    extract_statement_period,
    parse_transactions,
)


def _unique_warnings(warnings: List[str]) -> List[str]:
    seen = set()
    result = []
    for warning in warnings:
        if warning and warning not in seen:
            seen.add(warning)
            result.append(warning)
    return result


async def analyze_kaspi_pdf(pdf_bytes: bytes) -> Dict[str, object]:
    text, pdf_warnings = extract_text_from_pdf(pdf_bytes)
    summary_values, summary_warnings = parse_kaspi_summary(text)
    transactions, transaction_warnings = parse_transactions(text)
    period = extract_statement_period(text)
    summary = calculate_summary(summary_values)
    chart_data = build_expense_chart_data(transactions, period)

    try:
        merchant_categories = await classify_merchants_with_ai(transactions)
        categories = build_categories_from_transactions(transactions, merchant_categories)
    except Exception as exc:
        print(f"[KaspiImport] AI category classification failed, using defaults: {exc}")
        categories = get_default_categories()

    return {
        "summary": summary,
        "transactions": transactions,
        "chartData": chart_data,
        "categories": categories,
        "requiredCategories": [],
        "warnings": _unique_warnings([
            *pdf_warnings,
            *summary_warnings,
            *transaction_warnings,
        ]),
    }
