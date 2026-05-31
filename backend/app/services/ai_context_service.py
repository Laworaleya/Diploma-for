from app.models.ai_chat import (
    ExpenseCategoryAIContext,
    FinancialReportAIContext,
    FinancialReportSummaryAIContext,
    GoalAIContext,
    RecurringPaymentAIContext,
    RequiredCategoryAIContext,
)


def build_recurring_payment_context(payments: list[dict]) -> list[RecurringPaymentAIContext]:
    return [
        RecurringPaymentAIContext(
            title=payment.get("title", ""),
            amount=float(payment.get("amount", 0) or 0),
            period=payment.get("period", "monthly"),
            nextPaymentDate=payment.get("nextPaymentDate"),
            status=payment.get("status"),
            source=payment.get("source"),
        )
        for payment in payments
        if payment.get("title")
    ]


def build_report_context(report: dict, recurring_payments: list[dict]) -> FinancialReportAIContext:
    return FinancialReportAIContext(
        period=report.get("period", ""),
        total_income=float(report.get("total_income", 0) or 0),
        total_expense=float(report.get("total_expense", 0) or 0),
        unaccounted_expense=float(report.get("unaccounted_expense", 0) or 0),
        surplus=float(report.get("surplus", 0) or 0),
        categories=[
            ExpenseCategoryAIContext(
                name=category.get("name", ""),
                amount=float(category.get("amount", 0) or 0),
                custom=bool(category.get("custom", False)),
            )
            for category in report.get("categories", [])
            if category.get("name")
        ],
        required_categories=[
            RequiredCategoryAIContext(
                name=category.get("name", ""),
                amount=float(category.get("amount", 0) or 0),
                period=category.get("period", "monthly"),
                duration=category.get("duration"),
                paymentDate=category.get("paymentDate"),
            )
            for category in report.get("required_categories", [])
            if category.get("name")
        ],
        recurring_payments=build_recurring_payment_context(recurring_payments),
    )


def build_report_summary_context(report: dict) -> FinancialReportSummaryAIContext:
    return FinancialReportSummaryAIContext(
        period=report.get("period", ""),
        total_income=float(report.get("total_income", 0) or 0),
        total_expense=float(report.get("total_expense", 0) or 0),
        unaccounted_expense=float(report.get("unaccounted_expense", 0) or 0),
        surplus=float(report.get("surplus", 0) or 0),
        categories=[
            ExpenseCategoryAIContext(
                name=category.get("name", ""),
                amount=float(category.get("amount", 0) or 0),
                custom=bool(category.get("custom", False)),
            )
            for category in report.get("categories", [])
            if category.get("name")
        ],
    )


def build_goal_context(
    goal: dict,
    recent_reports: list[dict],
    recurring_payments: list[dict],
) -> GoalAIContext:
    return GoalAIContext(
        title=goal.get("title", ""),
        goal_type=goal.get("goal_type", ""),
        target_amount=float(goal.get("target_amount", 0) or 0),
        current_amount=float(goal.get("current_amount", 0) or 0),
        progress_percent=float(goal.get("progress_percent", 0) or 0),
        deadline=goal.get("deadline"),
        description=goal.get("description"),
        status=goal.get("status"),
        recent_reports=[build_report_summary_context(report) for report in recent_reports],
        recurring_payments=build_recurring_payment_context(recurring_payments),
    )
