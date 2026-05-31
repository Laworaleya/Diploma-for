from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from app.models.report import ReportCreate, ReportUpdate
from app.services import report_service
from app.services.balance_service import calculate_balance
from app.services.kaspi_import import analyze_kaspi_pdf
from app.core.dependencies import get_current_user
from app.repositories import admin_repo

router = APIRouter(prefix="/api/reports", tags=["Financial Reports"])


@router.post("")
async def create_report(
    data: ReportCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new financial report for a given month."""
    return await report_service.create_report(current_user["id"], data)


@router.get("")
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List all financial reports for the current user."""
    return await report_service.get_user_reports(current_user["id"], skip, limit)


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific financial report."""
    return await report_service.get_report(report_id, current_user["id"])


@router.put("/{report_id}")
async def update_report(
    report_id: str,
    data: ReportUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a financial report. Recalculates balance automatically."""
    return await report_service.update_report(report_id, current_user["id"], data)


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a financial report."""
    await report_service.delete_report(report_id, current_user["id"])
    return {"detail": "Report deleted"}


@router.post("/calculate-balance")
async def calculate_balance_preview(
    data: ReportCreate,
    current_user: dict = Depends(get_current_user),
):
    """Preview balance calculation without saving the report."""
    categories = [cat.model_dump() for cat in data.categories]
    return calculate_balance(data.total_income, data.total_expense, categories)


@router.post("/import-kaspi-pdf")
async def import_kaspi_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Parse a Kaspi Bank PDF statement and return extracted finance data."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Загрузите PDF-файл")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="PDF-файл пустой")

    try:
        result = await analyze_kaspi_pdf(pdf_bytes)
        await admin_repo.log_kaspi_import(current_user["id"], file.filename or "unknown.pdf")
        return result
    except ValueError as exc:
        await admin_repo.log_import_error(
            current_user["id"], file.filename or "unknown.pdf", str(exc)
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
