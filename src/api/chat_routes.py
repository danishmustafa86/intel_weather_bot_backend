"""ChatGPT-style chat endpoints: create, list, open, rename, delete chats,
ask follow-up questions, edit a question, and regenerate the last answer."""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from src.agent.agent import run_agent
from src.database import chat_repository as repo
from src.database.schemas import (
    Chat,
    ChatReply,
    ChatSummary,
    CreateChatRequest,
    DeleteResponse,
    EditMessageRequest,
    Message,
    RenameChatRequest,
    SendMessageRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])

# How many previous messages are sent to the model as context.
HISTORY_WINDOW = 20


async def _get_chat_or_404(chat_id: str) -> Chat:
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat not found")
    return chat


async def _answer(question: str, history: list[Message]) -> str:
    context = [m.model_dump() for m in history[-HISTORY_WINDOW:]]
    try:
        return await run_agent(question, context)
    except Exception as exc:
        logger.exception("Agent failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"The AI agent failed to answer (all configured models errored): {exc}",
        ) from exc


async def _ask_in_chat(chat: Chat, question: str) -> ChatReply:
    answer = await _answer(question, chat.messages)
    user_msg = Message(role="user", content=question)
    ai_msg = Message(role="assistant", content=answer)

    # First question of an untitled chat becomes its title
    new_title = None
    if not chat.messages and chat.title == repo.DEFAULT_TITLE:
        new_title = repo.make_title(question)

    await repo.append_messages(chat.id, [user_msg, ai_msg], title=new_title)
    return ChatReply(chat_id=chat.id, user_message=user_msg, assistant_message=ai_msg)


# ----------------------------- chats -----------------------------

@router.post("", response_model=Chat, status_code=status.HTTP_201_CREATED)
async def create_chat(body: CreateChatRequest):
    """Start a new chat. If `message` is given, the agent answers it right away."""
    chat = await repo.create_chat(body.title)
    if body.message and body.message.strip():
        try:
            await _ask_in_chat(chat, body.message.strip())
        except HTTPException:
            await repo.delete_chat(chat.id)  # don't leave an empty chat behind
            raise
    return await _get_chat_or_404(chat.id)


@router.get("", response_model=list[ChatSummary])
async def list_chats(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    """List chats, most recently updated first (for the sidebar)."""
    return await repo.list_chats(skip=skip, limit=limit)


@router.get("/{chat_id}", response_model=Chat)
async def get_chat(chat_id: str):
    """Open a chat with its full message history."""
    return await _get_chat_or_404(chat_id)


@router.patch("/{chat_id}", response_model=Chat)
async def rename_chat(chat_id: str, body: RenameChatRequest):
    """Rename a chat."""
    chat = await repo.rename_chat(chat_id, body.title.strip())
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat not found")
    return chat


@router.delete("/{chat_id}", response_model=DeleteResponse)
async def delete_chat(chat_id: str):
    """Delete one chat."""
    deleted = await repo.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat not found")
    return DeleteResponse(deleted=deleted)


@router.delete("", response_model=DeleteResponse)
async def delete_all_chats():
    """Delete ALL chats."""
    return DeleteResponse(deleted=await repo.delete_all_chats())


# ---------------------------- messages ---------------------------

@router.post("/{chat_id}/messages", response_model=ChatReply)
async def send_message(chat_id: str, body: SendMessageRequest):
    """Ask a (follow-up) question inside an existing chat."""
    chat = await _get_chat_or_404(chat_id)
    return await _ask_in_chat(chat, body.message.strip())


@router.put("/{chat_id}/messages/{message_id}", response_model=Chat)
async def edit_message(chat_id: str, message_id: str, body: EditMessageRequest):
    """Edit one of your questions. Like ChatGPT, every message after it is
    removed and the agent answers the edited question again."""
    chat = await _get_chat_or_404(chat_id)
    idx = next((i for i, m in enumerate(chat.messages) if m.id == message_id), None)
    if idx is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    if chat.messages[idx].role != "user":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only user messages can be edited")

    history = chat.messages[:idx]
    question = body.message.strip()
    answer = await _answer(question, history)

    edited = Message(id=message_id, role="user", content=question)
    reply = Message(role="assistant", content=answer)
    await repo.replace_messages(chat_id, [*history, edited, reply])
    return await _get_chat_or_404(chat_id)


@router.post("/{chat_id}/regenerate", response_model=Chat)
async def regenerate_last_answer(chat_id: str):
    """Generate a new answer for the last question in the chat."""
    chat = await _get_chat_or_404(chat_id)
    last_user_idx = next(
        (i for i in range(len(chat.messages) - 1, -1, -1) if chat.messages[i].role == "user"),
        None,
    )
    if last_user_idx is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No question to regenerate")

    history = chat.messages[:last_user_idx]
    question = chat.messages[last_user_idx]
    answer = await _answer(question.content, history)

    reply = Message(role="assistant", content=answer)
    await repo.replace_messages(chat_id, [*history, question, reply])
    return await _get_chat_or_404(chat_id)


@router.delete("/{chat_id}/messages/{message_id}", response_model=DeleteResponse)
async def delete_message(chat_id: str, message_id: str):
    """Delete a single message from a chat."""
    await _get_chat_or_404(chat_id)
    if not await repo.delete_message(chat_id, message_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    return DeleteResponse(deleted=1)
