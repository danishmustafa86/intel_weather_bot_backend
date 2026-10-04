"""CRUD operations for chats and their messages."""

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from src.database.connection import get_chats_collection
from src.database.schemas import Chat, ChatSummary, Message, utc_now

DEFAULT_TITLE = "New chat"


def _oid(chat_id: str) -> ObjectId | None:
    try:
        return ObjectId(chat_id)
    except (InvalidId, TypeError):
        return None


def _to_chat(doc: dict) -> Chat:
    return Chat(
        id=str(doc["_id"]),
        title=doc["title"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        messages=[Message(**m) for m in doc.get("messages", [])],
    )


def make_title(text: str, max_len: int = 50) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"


async def create_chat(title: str | None = None) -> Chat:
    now = utc_now()
    doc = {"title": title or DEFAULT_TITLE, "created_at": now, "updated_at": now, "messages": []}
    result = await get_chats_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_chat(doc)


async def list_chats(skip: int = 0, limit: int = 50) -> list[ChatSummary]:
    pipeline = [
        {"$sort": {"updated_at": -1}},
        {"$skip": skip},
        {"$limit": limit},
        {"$project": {
            "title": 1, "created_at": 1, "updated_at": 1,
            "message_count": {"$size": {"$ifNull": ["$messages", []]}},
        }},
    ]
    cursor = await get_chats_collection().aggregate(pipeline)
    return [
        ChatSummary(
            id=str(d["_id"]),
            title=d["title"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            message_count=d["message_count"],
        )
        async for d in cursor
    ]


async def get_chat(chat_id: str) -> Chat | None:
    oid = _oid(chat_id)
    if oid is None:
        return None
    doc = await get_chats_collection().find_one({"_id": oid})
    return _to_chat(doc) if doc else None


async def rename_chat(chat_id: str, title: str) -> Chat | None:
    oid = _oid(chat_id)
    if oid is None:
        return None
    doc = await get_chats_collection().find_one_and_update(
        {"_id": oid},
        {"$set": {"title": title, "updated_at": utc_now()}},
        return_document=ReturnDocument.AFTER,
    )
    return _to_chat(doc) if doc else None


async def append_messages(chat_id: str, messages: list[Message], title: str | None = None) -> bool:
    oid = _oid(chat_id)
    if oid is None:
        return False
    update: dict = {
        "$push": {"messages": {"$each": [m.model_dump() for m in messages]}},
        "$set": {"updated_at": utc_now()},
    }
    if title:
        update["$set"]["title"] = title
    result = await get_chats_collection().update_one({"_id": oid}, update)
    return result.matched_count == 1


async def replace_messages(chat_id: str, messages: list[Message]) -> bool:
    """Overwrite the whole message list (used when a message is edited)."""
    oid = _oid(chat_id)
    if oid is None:
        return False
    result = await get_chats_collection().update_one(
        {"_id": oid},
        {"$set": {"messages": [m.model_dump() for m in messages], "updated_at": utc_now()}},
    )
    return result.matched_count == 1


async def delete_message(chat_id: str, message_id: str) -> bool:
    oid = _oid(chat_id)
    if oid is None:
        return False
    result = await get_chats_collection().update_one(
        {"_id": oid},
        {"$pull": {"messages": {"id": message_id}}, "$set": {"updated_at": utc_now()}},
    )
    return result.modified_count == 1


async def delete_chat(chat_id: str) -> int:
    oid = _oid(chat_id)
    if oid is None:
        return 0
    result = await get_chats_collection().delete_one({"_id": oid})
    return result.deleted_count


async def delete_all_chats() -> int:
    result = await get_chats_collection().delete_many({})
    return result.deleted_count
