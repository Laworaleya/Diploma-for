from fastapi import HTTPException, status
from app.repositories import report_repo
from app.services.balance_service import calculate_balance
from app.models.report import ReportCreate, ReportUpdate
from app.services.recurring_payment_service import sync_required_categories


async def create_report(user_id: str, data: ReportCreate) -> dict:
    """Create a new financial report with auto-calculated balance fields."""
    categories = [cat.model_dump() for cat in data.categories]
    required_categories = [cat.model_dump() for cat in data.required_categories]
    balance = calculate_balance(data.total_income, data.total_expense, categories)

    report_data = {
        "user_id": user_id,
        "period": data.period,
        "total_income": data.total_income,
        "total_expense": data.total_expense,
        "categories": categories,
        "required_categories": required_categories,
        "unaccounted_expense": balance["unaccounted_expense"],
        "surplus": balance["surplus"],
    }

    report = await report_repo.create_report(report_data)
    await sync_required_categories(user_id, required_categories)
    return report


async def get_user_reports(user_id: str, skip: int = 0, limit: int = 20) -> list:
    """Get all reports for a user."""
    return await report_repo.find_reports_by_user(user_id, skip, limit)


async def get_report(report_id: str, user_id: str) -> dict:
    """Get a specific report."""
    report = await report_repo.find_report_by_id(report_id, user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


async def update_report(report_id: str, user_id: str, data: ReportUpdate) -> dict:
    """Update a financial report, recalculating balance fields."""
    existing = await report_repo.find_report_by_id(report_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")

    # Merge updates
    income = data.total_income if data.total_income is not None else existing["total_income"]
    expense = data.total_expense if data.total_expense is not None else existing["total_expense"]
    categories = (
        [cat.model_dump() for cat in data.categories]
        if data.categories is not None
        else existing.get("categories", [])
    )
    required_categories = (
        [cat.model_dump() for cat in data.required_categories]
        if data.required_categories is not None
        else existing.get("required_categories", [])
    )

    balance = calculate_balance(income, expense, categories)

    update_data = {
        "period": data.period if data.period is not None else existing["period"],
        "total_income": income,
        "total_expense": expense,
        "categories": categories,
        "required_categories": required_categories,
        "unaccounted_expense": balance["unaccounted_expense"],
        "surplus": balance["surplus"],
    }

    report = await report_repo.update_report(report_id, user_id, update_data)
    await sync_required_categories(user_id, required_categories)
    return report


async def delete_report(report_id: str, user_id: str) -> bool:
    """Delete a financial report."""
    deleted = await report_repo.delete_report(report_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return True
