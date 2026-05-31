from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from app.core.database import get_database


def _serialize_doc(doc: dict) -> dict:
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


def _duplicate_filter(user_id: str, data: dict) -> dict:
    return {
        "user_id": user_id,
        "title_key": data["title"].strip().lower(),
        "amount": data["amount"],
        "originalPaymentDate": data["originalPaymentDate"],
        "period": data["period"],
    }


async def find_duplicate(user_id: str, data: dict) -> Optional[dict]:
    db = get_database()
    doc = await db.recurring_payments.find_one(_duplicate_filter(user_id, data))
    if not doc:
        return None
    serialized = _serialize_doc(doc)
    serialized.pop("title_key", None)
    return serialized


async def create_payment(payment_data: dict) -> dict:
    db = get_database()
    now = datetime.now(timezone.utc)
    payment_data["title_key"] = payment_data["title"].strip().lower()
    payment_data["created_at"] = now
    payment_data["updated_at"] = now
    result = await db.recurring_payments.insert_one(payment_data)
    payment_data["id"] = str(result.inserted_id)
    payment_data.pop("_id", None)
    payment_data["created_at"] = now.isoformat()
    payment_data["updated_at"] = now.isoformat()
    payment_data.pop("title_key", None)
    return payment_data


async def find_payments_by_user(user_id: str) -> List[dict]:
    db = get_database()
    cursor = db.recurring_payments.find({"user_id": user_id}).sort("nextPaymentDate", 1)
    payments = []
    async for payment in cursor:
        serialized = _serialize_doc(payment)
        serialized.pop("title_key", None)
        payments.append(serialized)
    return payments


async def find_payment_by_id(payment_id: str, user_id: str) -> Optional[dict]:
    db = get_database()
    try:
        payment = await db.recurring_payments.find_one({
            "_id": ObjectId(payment_id),
            "user_id": user_id,
        })
    except Exception:
        return None
    if not payment:
        return None
    serialized = _serialize_doc(payment)
    serialized.pop("title_key", None)
    return serialized


async def update_payment(payment_id: str, user_id: str, update_data: dict) -> Optional[dict]:
    db = get_database()
    update_data["title_key"] = update_data["title"].strip().lower()
    update_data["updated_at"] = datetime.now(timezone.utc)
    try:
        result = await db.recurring_payments.find_one_and_update(
            {"_id": ObjectId(payment_id), "user_id": user_id},
            {"$set": update_data},
            return_document=True,
        )
    except Exception:
        return None
    if not result:
        return None
    serialized = _serialize_doc(result)
    serialized.pop("title_key", None)
    return serialized


async def delete_payment(payment_id: str, user_id: str) -> bool:
    db = get_database()
    try:
        result = await db.recurring_payments.delete_one({
            "_id": ObjectId(payment_id),
            "user_id": user_id,
        })
        return result.deleted_count > 0
    except Exception:
        return False
