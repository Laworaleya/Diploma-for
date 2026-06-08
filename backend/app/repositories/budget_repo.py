from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.core.database import get_database


def _serialize_doc(doc: dict) -> dict:
    if doc is None:
        return None
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    for key, value in list(doc.items()):
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
        elif isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc


async def get_or_create_budget(user_id: str, period: str) -> dict:
    """Get or create a budget document for the given YYYY-MM period."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "period": period,
                "monthly_limit": 0.0,
                "total_income": 0.0,
                "total_expense": 0.0,
                "created_at": now,
                "updated_at": now,
            }
        },
        upsert=True,
        return_document=True,
    )
    result = _serialize_doc(doc)
    result["current_balance"] = result["total_income"] - result["total_expense"]
    return result


async def set_monthly_limit(user_id: str, period: str, limit: float) -> dict:
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {"$set": {"monthly_limit": limit, "updated_at": now}},
        upsert=True,
        return_document=True,
    )
    result = _serialize_doc(doc)
    result["current_balance"] = result["total_income"] - result["total_expense"]
    return result


async def add_income(user_id: str, period: str, amount: float) -> dict:
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {
            "$inc": {"total_income": amount},
            "$set": {"updated_at": now},
            "$setOnInsert": {
                "monthly_limit": amount,
                "total_expense": 0.0,
                "created_at": now,
            },
        },
        upsert=True,
        return_document=True,
    )
    result = _serialize_doc(doc)
    result["current_balance"] = result["total_income"] - result["total_expense"]
    return result


async def add_expense(user_id: str, period: str, amount: float) -> dict:
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {
            "$inc": {"total_expense": amount},
            "$set": {"updated_at": now},
            "$setOnInsert": {
                "monthly_limit": 0.0,
                "total_income": 0.0,
                "created_at": now,
            },
        },
        upsert=True,
        return_document=True,
    )
    result = _serialize_doc(doc)
    result["current_balance"] = result["total_income"] - result["total_expense"]
    return result


async def get_current_balance(user_id: str, period: str) -> float:
    db = get_database()
    doc = await db.user_budgets.find_one({"user_id": user_id, "period": period})
    if not doc:
        return 0.0
    return doc.get("total_income", 0.0) - doc.get("total_expense", 0.0)
