from datetime import datetime, timezone

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


async def get_all_users_with_stats(skip: int = 0, limit: int = 50) -> list[dict]:
    db = get_database()
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": limit},
        {"$project": {"hashed_password": 0}},
        {
            "$lookup": {
                "from": "financial_reports",
                "let": {"uid": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$user_id", "$$uid"]}}},
                    {"$count": "count"},
                ],
                "as": "report_counts",
            }
        },
        {
            "$addFields": {
                "report_count": {
                    "$ifNull": [{"$arrayElemAt": ["$report_counts.count", 0]}, 0]
                }
            }
        },
        {"$project": {"report_counts": 0}},
    ]
    users = []
    async for doc in db.users.aggregate(pipeline):
        users.append(_serialize_doc(doc))
    return users


async def block_user(user_id: str) -> bool:
    db = get_database()
    try:
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_blocked": True}},
        )
        return result.matched_count > 0
    except Exception:
        return False


async def delete_user_and_data(user_id: str) -> bool:
    db = get_database()
    try:
        await db.ai_messages.delete_many({"user_id": user_id})
        await db.ai_chats.delete_many({"user_id": user_id})
        await db.financial_reports.delete_many({"user_id": user_id})
        await db.financial_goals.delete_many({"user_id": user_id})
        await db.recurring_payments.delete_many({"user_id": user_id})
        result = await db.users.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
    except Exception:
        return False


async def get_global_stats() -> dict:
    db = get_database()
    users_count, reports_count, kaspi_count, chats_count = await _gather(
        db.users.count_documents({}),
        db.financial_reports.count_documents({}),
        db.kaspi_imports.count_documents({}),
        db.ai_chats.count_documents({}),
    )
    return {
        "total_users": users_count,
        "total_reports": reports_count,
        "total_kaspi_imports": kaspi_count,
        "total_ai_chats": chats_count,
    }


async def get_ai_stats() -> dict:
    db = get_database()
    error_count = await db.ai_errors.count_documents({})

    pipeline = [
        {
            "$match": {
                "role": "user",
                "content": {"$not": {"$regex": "^Проанализируй финансовый отчет|^Составь план"}},
            }
        },
        {"$group": {"_id": "$content", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "question": "$_id", "count": 1}},
    ]
    top_questions = []
    async for doc in db.ai_messages.aggregate(pipeline):
        top_questions.append(doc)

    return {
        "total_ai_errors": error_count,
        "top_questions": top_questions,
    }


async def get_import_errors(limit: int = 50) -> list[dict]:
    db = get_database()
    cursor = db.import_errors.find({}).sort("created_at", -1).limit(limit)
    errors = []
    async for doc in cursor:
        errors.append(_serialize_doc(doc))
    return errors


async def log_kaspi_import(user_id: str, filename: str) -> None:
    db = get_database()
    await db.kaspi_imports.insert_one(
        {
            "user_id": user_id,
            "filename": filename,
            "created_at": datetime.now(timezone.utc),
        }
    )


async def log_import_error(user_id: str, filename: str, error_message: str) -> None:
    db = get_database()
    await db.import_errors.insert_one(
        {
            "user_id": user_id,
            "filename": filename,
            "error_message": error_message,
            "created_at": datetime.now(timezone.utc),
        }
    )


async def log_ai_error(user_id: str, error_type: str, message: str) -> None:
    db = get_database()
    await db.ai_errors.insert_one(
        {
            "user_id": user_id,
            "error_type": error_type,
            "message": message,
            "created_at": datetime.now(timezone.utc),
        }
    )


async def _gather(*coros):
    import asyncio
    return await asyncio.gather(*coros)
