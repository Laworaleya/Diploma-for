"""Shared async MongoDB connection for the bot process."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from dotenv import load_dotenv

_bot_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_bot_dir)
_project_dir = os.path.dirname(_backend_dir)
load_dotenv(os.path.join(_backend_dir, ".env"))
load_dotenv(os.path.join(_project_dir, ".env"))

_MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/financial_literacy")
_MONGODB_DB = os.getenv("MONGODB_DB_NAME", "financial_literacy")

_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None


async def connect():
    global _client, _database
    _client = AsyncIOMotorClient(_MONGODB_URI)
    _database = _client[_MONGODB_DB]


async def close():
    global _client
    if _client:
        _client.close()


def get_db() -> AsyncIOMotorDatabase:
    return _database
