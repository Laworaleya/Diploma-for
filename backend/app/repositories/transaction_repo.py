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


async def create_transaction(
    user_id: str,
    type: str,
    amount: float,
    category: str,
    description: Optional[str] = None,
) -> dict:
    db = get_database()
    doc = {
        "user_id": user_id,
        "type": type,
        "amount": amount,
        "category": category,
        "description": description,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.transactions.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    doc["created_at"] = doc["created_at"].isoformat()
    return doc


async def get_transactions(user_id: str, since: datetime, until: datetime) -> list:
    db = get_database()
    cursor = db.transactions.find(
        {"user_id": user_id, "created_at": {"$gte": since, "$lte": until}},
    ).sort("created_at", -1)
    result = []
    async for doc in cursor:
        result.append(_serialize_doc(doc))
    return result


async def get_period_total(user_id: str, since: datetime, until: datetime, type: str) -> float:
    db = get_database()
    pipeline = [
        {"$match": {"user_id": user_id, "type": type, "created_at": {"$gte": since, "$lte": until}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    async for doc in db.transactions.aggregate(pipeline):
        return doc["total"]
    return 0.0


async def get_spending_by_category(user_id: str, since: datetime, until: datetime) -> dict:
    """Returns {category: total_amount} for expense transactions in the period."""
    db = get_database()
    pipeline = [
        {"$match": {"user_id": user_id, "type": "expense", "created_at": {"$gte": since, "$lte": until}}},
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
        {"$sort": {"total": -1}},
    ]
    result = {}
    async for doc in db.transactions.aggregate(pipeline):
        result[doc["_id"]] = doc["total"]
    return result
