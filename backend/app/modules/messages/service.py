import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.images import compress_image, image_dimensions, make_thumbnail
from app.core.storage import put_object
from app.modules.messages.models import (
    MSG_AUDIO,
    MSG_FILE,
    MSG_IMAGE,
    MSG_TEXT,
    MSG_VIDEO,
    MSG_VOICE,
    Attachment,
    Message,
)
from app.modules.messages.schemas import MessageCreate, MessagePage, MessageRead
from app.modules.users.models import User

MAX_PAGE = 50
MAX_ATTACHMENT_BYTES = 100 * 1024 * 1024


def _now() -> datetime:
    return datetime.now(UTC)


def process_blob(
    prefix: str, data: bytes, mime: str, as_file: bool = False
) -> dict[str, Any]:
    """Sync (CPU + network) blob work — call via a thread. Stores original +
    (for inline images) a thumbnail under ``prefix`` and returns storage
    metadata. When as_file is set the blob is treated as a plain download —
    no thumbnail/dimensions."""
    key = f"{prefix}/{uuid.uuid4().hex}"
    width = height = None
    thumb_key = None
    if mime.startswith("image/") and not as_file:
        data, mime = compress_image(data, mime)
        dims = image_dimensions(data)
        if dims:
            width, height = dims
        thumb = make_thumbnail(data)
        if thumb:
            thumb_key = f"{prefix}/thumb/{uuid.uuid4().hex}.jpg"
            put_object(thumb_key, thumb, "image/jpeg")
    put_object(key, data, mime)
    # Return the *effective* mime/size of the stored bytes (compression may have
    # changed both) so the DB row matches the object, not the upload.
    return {
        "storage_key": key,
        "thumbnail_key": thumb_key,
        "width": width,
        "height": height,
        "mime": mime,
        "size": len(data),
    }


async def record_attachment(
    db: AsyncSession,
    chat_id: uuid.UUID | None,
    uploader: User,
    name: str,
    mime: str,
    size: int,
    meta: dict[str, Any],
    *,
    as_file: bool = False,
    is_voice: bool = False,
    duration_ms: int | None = None,
) -> Attachment:
    attachment = Attachment(
        chat_id=chat_id,
        uploader_id=uploader.id,
        name=name[:255],
        mime=mime,
        size=size,
        storage_key=meta["storage_key"],
        thumbnail_key=meta["thumbnail_key"],
        width=meta["width"],
        height=meta["height"],
        as_file=as_file,
        is_voice=is_voice,
        duration_ms=duration_ms,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


def _derive_type(attachments: list[Attachment]) -> str:
    """Message type hint from its attachments (first one wins for the icon)."""
    if not attachments:
        return MSG_TEXT
    att = attachments[0]
    if att.is_voice:
        return MSG_VOICE
    if att.as_file:
        return MSG_FILE
    if att.mime.startswith("image/"):
        return MSG_IMAGE
    if att.mime.startswith("video/"):
        return MSG_VIDEO
    if att.mime.startswith("audio/"):
        return MSG_AUDIO
    return MSG_FILE


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

    attachments: list[Attachment] = []
    if data.attachment_ids:
        for aid in data.attachment_ids:
            att = await db.get(Attachment, aid)
            if (
                att is None
                or att.chat_id != chat_id
                or att.uploader_id != sender.id
                or att.message_id is not None
            ):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid attachment")
            attachments.append(att)

    msg_type = _derive_type(attachments)

    message = Message(
        chat_id=chat_id,
        sender_id=sender.id,
        type=msg_type,
        content=data.content,
        reply_to_id=data.reply_to_id,
    )
    db.add(message)
    await db.flush()  # assign message.id
    for att in attachments:
        att.message_id = message.id
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
