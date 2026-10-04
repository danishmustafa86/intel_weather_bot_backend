"""MongoDB connection (PyMongo async client) and collection setup."""

import logging

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from src.config import get_settings

logger = logging.getLogger(__name__)

CHATS_COLLECTION = "chats"

_client: AsyncMongoClient | None = None


async def connect_to_mongo() -> None:
    global _client
    settings = get_settings()
    _client = AsyncMongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    await _client.admin.command("ping")
    await create_indexes()
    logger.info("Connected to MongoDB database '%s'", settings.mongodb_db_name)


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_database() -> AsyncDatabase:
    if _client is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongo() first.")
    return _client[get_settings().mongodb_db_name]


def get_chats_collection() -> AsyncCollection:
    return get_database()[CHATS_COLLECTION]


async def create_indexes() -> None:
    chats = get_chats_collection()
    # Sidebar lists chats newest first
    await chats.create_index([("updated_at", DESCENDING)])
    await chats.create_index([("messages.id", ASCENDING)])
