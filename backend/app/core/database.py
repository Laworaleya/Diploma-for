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
    await _database.users.create_index("email", unique=True)
    await _database.financial_reports.create_index([("user_id", 1), ("period", -1)])
    await _database.financial_goals.create_index("user_id")
    await _database.ai_chats.create_index([("user_id", 1), ("updated_at", -1)])
    await _database.ai_messages.create_index([("chat_id", 1), ("created_at", 1)])

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
