from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from app.core.database import get_database


def _serialize_doc(doc: dict | None) -> dict | None:
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


async def create_chat(chat_data: dict) -> dict:
    db = get_database()
    now = datetime.now(timezone.utc)
    chat_data["created_at"] = now
    chat_data["updated_at"] = now
    result = await db.ai_chats.insert_one(chat_data)
    chat_data["id"] = str(result.inserted_id)
    chat_data.pop("_id", None)
    chat_data["created_at"] = now.isoformat()
    chat_data["updated_at"] = now.isoformat()
    return chat_data


async def find_chats_by_user(user_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
    db = get_database()
    cursor = (
        db.ai_chats.find({"user_id": user_id}, {"openai_thread_id": 0})
        .sort("updated_at", -1)
        .skip(skip)
        .limit(limit)
    )
    chats = []
    async for chat in cursor:
        serialized = _serialize_doc(chat)
        serialized.pop("user_id", None)
        chats.append(serialized)
    return chats


async def find_chat_by_id(chat_id: str, user_id: str) -> Optional[dict]:
    db = get_database()
    try:
        chat = await db.ai_chats.find_one({"_id": ObjectId(chat_id), "user_id": user_id})
    except Exception:
        return None
    return _serialize_doc(chat) if chat else None


async def update_chat(chat_id: str, user_id: str, update_data: dict) -> Optional[dict]:
    db = get_database()
    update_data["updated_at"] = datetime.now(timezone.utc)
    try:
        chat = await db.ai_chats.find_one_and_update(
            {"_id": ObjectId(chat_id), "user_id": user_id},
            {"$set": update_data},
            return_document=True,
        )
    except Exception:
        return None
    return _serialize_doc(chat) if chat else None


async def touch_chat(chat_id: str, user_id: str) -> None:
    db = get_database()
    try:
        await db.ai_chats.update_one(
            {"_id": ObjectId(chat_id), "user_id": user_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}},
        )
    except Exception:
        return


async def create_message(message_data: dict) -> dict:
    db = get_database()
    now = datetime.now(timezone.utc)
    message_data["created_at"] = now
    result = await db.ai_messages.insert_one(message_data)
    message_data["id"] = str(result.inserted_id)
    message_data.pop("_id", None)
    message_data["created_at"] = now.isoformat()
    return message_data


async def find_messages_by_chat(chat_id: str, user_id: str) -> list[dict]:
    db = get_database()
    cursor = db.ai_messages.find({"chat_id": chat_id, "user_id": user_id}).sort("created_at", 1)
    messages = []
    async for message in cursor:
        serialized = _serialize_doc(message)
        serialized.pop("user_id", None)
        messages.append(serialized)
    return messages


async def delete_messages_by_chat(chat_id: str) -> int:
    db = get_database()
    try:
        result = await db.ai_messages.delete_many({"chat_id": chat_id})
        return result.deleted_count
    except Exception:
        return 0


async def delete_chat(chat_id: str, user_id: str) -> bool:
    db = get_database()
    try:
        result = await db.ai_chats.delete_one({"_id": ObjectId(chat_id), "user_id": user_id})
        return result.deleted_count > 0
    except Exception:
        return False
