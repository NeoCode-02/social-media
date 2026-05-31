import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.messages.models import MSG_TEXT, Message
from app.modules.messages.schemas import MessageCreate, MessagePage, MessageRead
from app.modules.users.models import User

MAX_PAGE = 50


def _now() -> datetime:
    return datetime.now(UTC)


async def list_messages(
    db: AsyncSession,
    chat_id: uuid.UUID,
    limit: int = 30,
    before: uuid.UUID | None = None,
) -> MessagePage:
    limit = max(1, min(limit, MAX_PAGE))
    # UUIDv7 ids sort chronologically, so id is the cursor (newest first).
    q = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.id.desc())
        .limit(limit + 1)
    )
    if before is not None:
        q = q.where(Message.id < before)
    rows = list((await db.scalars(q)).all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = str(rows[-1].id) if has_more and rows else None
    return MessagePage(
        messages=[MessageRead.model_validate(r) for r in rows],
        next_cursor=next_cursor,
    )


async def create_message(
    db: AsyncSession, chat_id: uuid.UUID, sender: User, data: MessageCreate
) -> Message:
    if data.reply_to_id is not None:
        reply = await db.get(Message, data.reply_to_id)
        if reply is None or reply.chat_id != chat_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid reply target")
    message = Message(
        chat_id=chat_id,
        sender_id=sender.id,
        type=MSG_TEXT,
        content=data.content,
        reply_to_id=data.reply_to_id,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def _owned_message(db: AsyncSession, message_id: uuid.UUID, user: User) -> Message:
    message = await db.get(Message, message_id)
    if message is None or message.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    if message.sender_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your message")
    return message


async def edit_message(
    db: AsyncSession, message_id: uuid.UUID, user: User, content: str
) -> Message:
    message = await _owned_message(db, message_id, user)
    message.content = content
    message.edited_at = _now()
    await db.commit()
    await db.refresh(message)
    return message


async def delete_message(db: AsyncSession, message_id: uuid.UUID, user: User) -> Message:
    message = await _owned_message(db, message_id, user)
    message.deleted_at = _now()
    message.content = None
    await db.commit()
    await db.refresh(message)
    return message
