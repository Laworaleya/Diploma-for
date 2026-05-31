from datetime import datetime, timezone
from typing import Optional
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


async def create_user(user_data: dict) -> dict:
    """Insert a new user document."""
    db = get_database()
    user_data["created_at"] = datetime.now(timezone.utc)
    user_data["role"] = "user"
    result = await db.users.insert_one(user_data)
    user_data["id"] = str(result.inserted_id)
    user_data.pop("_id", None)
    user_data["created_at"] = user_data["created_at"].isoformat()
    return user_data


async def find_user_by_email(email: str) -> Optional[dict]:
    """Find user by email address."""
    db = get_database()
    user = await db.users.find_one({"email": email})
    return _serialize_doc(user) if user else None


async def find_user_by_id(user_id: str) -> Optional[dict]:
    """Find user by ID."""
    db = get_database()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    return _serialize_doc(user) if user else None


async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """Update user fields."""
    db = get_database()
    try:
        result = await db.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True,
        )
    except Exception:
        return None
    return _serialize_doc(result) if result else None


async def get_all_users(skip: int = 0, limit: int = 50) -> list:
    """Get all users (for admin). Returns anonymized data."""
    db = get_database()
    cursor = db.users.find(
        {},
        {"hashed_password": 0}
    ).skip(skip).limit(limit)
    users = []
    async for user in cursor:
        users.append(_serialize_doc(user))
    return users
