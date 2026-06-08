from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None


async def connect_db():
    """Initialize MongoDB connection on app startup."""
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _database = _client[settings.MONGODB_DB_NAME]

    # Create indexes
    # email must be sparse so Telegram-only users (no email) don't conflict
    try:
        await _database.users.create_index("email", unique=True, sparse=True)
    except Exception:
        # Old non-sparse index exists — drop and recreate as sparse
        await _database.users.drop_index("email_1")
        await _database.users.create_index("email", unique=True, sparse=True)
    await _database.users.create_index("telegram_id", unique=True, sparse=True)
    await _database.financial_reports.create_index([("user_id", 1), ("period", -1)])
    await _database.financial_goals.create_index("user_id")
    await _database.ai_chats.create_index([("user_id", 1), ("updated_at", -1)])
    await _database.ai_messages.create_index([("chat_id", 1), ("created_at", 1)])
    await _database.transactions.create_index([("user_id", 1), ("created_at", -1)])
    await _database.transactions.create_index([("user_id", 1), ("type", 1), ("created_at", -1)])
    await _database.user_budgets.create_index([("user_id", 1), ("period", -1)], unique=True)
    # Link codes: auto-expire after 10 minutes
    await _database.link_codes.create_index("created_at", expireAfterSeconds=600)
    await _database.link_codes.create_index("code", unique=True)

    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def close_db():
    """Close MongoDB connection on app shutdown."""
    global _client
    if _client:
        _client.close()
        print("🔌 MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return _database
