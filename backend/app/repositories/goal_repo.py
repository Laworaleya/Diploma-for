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


async def create_goal(goal_data: dict) -> dict:
    """Insert a new financial goal."""
    db = get_database()
    now = datetime.now(timezone.utc)
    goal_data["created_at"] = now
    goal_data["status"] = "active"
    result = await db.financial_goals.insert_one(goal_data)
    goal_data["id"] = str(result.inserted_id)
    goal_data.pop("_id", None)
    goal_data["created_at"] = now.isoformat()
    return goal_data


async def find_goals_by_user(user_id: str) -> List[dict]:
    """Get all goals for a user."""
    db = get_database()
    cursor = db.financial_goals.find({"user_id": user_id}).sort("created_at", -1)
    goals = []
    async for goal in cursor:
        goals.append(_serialize_doc(goal))
    return goals


async def find_goal_by_id(goal_id: str, user_id: str) -> Optional[dict]:
    """Get a specific goal by ID, scoped to user."""
    db = get_database()
    try:
        goal = await db.financial_goals.find_one({
            "_id": ObjectId(goal_id),
            "user_id": user_id,
        })
    except Exception:
        return None
    return _serialize_doc(goal) if goal else None


async def update_goal(goal_id: str, user_id: str, update_data: dict) -> Optional[dict]:
    """Update a financial goal."""
    db = get_database()
    update_data["updated_at"] = datetime.now(timezone.utc)
    try:
        result = await db.financial_goals.find_one_and_update(
            {"_id": ObjectId(goal_id), "user_id": user_id},
            {"$set": update_data},
            return_document=True,
        )
    except Exception:
        return None
    return _serialize_doc(result) if result else None


async def delete_goal(goal_id: str, user_id: str) -> bool:
    """Delete a financial goal."""
    db = get_database()
    try:
        result = await db.financial_goals.delete_one({
            "_id": ObjectId(goal_id),
            "user_id": user_id,
        })
        return result.deleted_count > 0
    except Exception:
        return False
