from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from app.core.database import get_database


def _serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
        elif isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc


async def create_report(report_data: dict) -> dict:
    """Insert a new financial report."""
    db = get_database()
    now = datetime.now(timezone.utc)
    report_data["created_at"] = now
    report_data["updated_at"] = now
    result = await db.financial_reports.insert_one(report_data)
    report_data["id"] = str(result.inserted_id)
    report_data.pop("_id", None)
    # Convert datetimes to strings
    report_data["created_at"] = now.isoformat()
    report_data["updated_at"] = now.isoformat()
    return report_data


async def find_reports_by_user(user_id: str, skip: int = 0, limit: int = 20) -> List[dict]:
    """Get all reports for a user, sorted by period descending."""
    db = get_database()
    cursor = db.financial_reports.find(
        {"user_id": user_id}
    ).sort("period", -1).skip(skip).limit(limit)
    reports = []
    async for report in cursor:
        reports.append(_serialize_doc(report))
    return reports


async def find_report_by_id(report_id: str, user_id: str) -> Optional[dict]:
    """Get a specific report by ID, scoped to user."""
    db = get_database()
    try:
        report = await db.financial_reports.find_one({
            "_id": ObjectId(report_id),
            "user_id": user_id,
        })
    except Exception:
        return None
    return _serialize_doc(report) if report else None


async def update_report(report_id: str, user_id: str, update_data: dict) -> Optional[dict]:
    """Update a financial report."""
    db = get_database()
    update_data["updated_at"] = datetime.now(timezone.utc)
    try:
        result = await db.financial_reports.find_one_and_update(
            {"_id": ObjectId(report_id), "user_id": user_id},
            {"$set": update_data},
            return_document=True,
        )
    except Exception:
        return None
    return _serialize_doc(result) if result else None


async def delete_report(report_id: str, user_id: str) -> bool:
    """Delete a financial report."""
    db = get_database()
    try:
        result = await db.financial_reports.delete_one({
            "_id": ObjectId(report_id),
            "user_id": user_id,
        })
        return result.deleted_count > 0
    except Exception:
        return False
