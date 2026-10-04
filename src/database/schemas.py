"""Schemas for the `chats` collection and the API request/response bodies.

MongoDB document shape (collection: chats):
{
    "_id": ObjectId,
    "title": str,
    "created_at": datetime,
    "updated_at": datetime,
    "messages": [
        {"id": str(uuid4), "role": "user" | "assistant", "content": str, "created_at": datetime},
        ...
    ]
}
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------- stored documents ----------------------

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class Chat(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message] = []


class ChatSummary(BaseModel):
    """Lightweight chat info for the sidebar list (no messages)."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


# ------------------------ API requests ------------------------

class CreateChatRequest(BaseModel):
    message: str | None = Field(
        None, description="Optional first question. If given, the agent answers it immediately."
    )
    title: str | None = Field(None, max_length=200)


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class EditMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class RenameChatRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


# ------------------------ API responses -----------------------

class ChatReply(BaseModel):
    chat_id: str
    user_message: Message
    assistant_message: Message


class DeleteResponse(BaseModel):
    deleted: int
