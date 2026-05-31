"""Realtime event publishing.

Events go onto a single Redis channel. The publisher computes the recipient
user ids (it has the DB session), so the cross-process listener can stay a dumb
dispatcher. (At larger scale, switch to per-chat channels to avoid every
instance receiving every event.)
"""

import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.modules.chats.models import ChatMember
from app.modules.follows.models import Follow
from app.modules.messages.schemas import MessageRead
from app.modules.posts.schemas import PostRead

CHANNEL = "realtime"


async def _chat_member_ids(db: AsyncSession, chat_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        (await db.scalars(select(ChatMember.user_id).where(ChatMember.chat_id == chat_id))).all()
    )


async def _co_member_ids(db: AsyncSession, user_id: uuid.UUID) -> set[uuid.UUID]:
    """All users who share at least one chat with ``user_id``."""
    my_chats = select(ChatMember.chat_id).where(ChatMember.user_id == user_id)
    rows = await db.scalars(
        select(ChatMember.user_id).where(ChatMember.chat_id.in_(my_chats)).distinct()
    )
    return set(rows.all())


async def _publish(recipients: list[uuid.UUID], event: dict[str, Any]) -> None:
    redis = get_redis()
    event_json = json.dumps(event)
    for user_id in recipients:
        await redis.publish(f"user:{user_id}", event_json)


async def publish_message_new(db: AsyncSession, chat_id: uuid.UUID, message: MessageRead) -> None:
    await _publish(
        await _chat_member_ids(db, chat_id),
        {
            "type": "message.new",
            "chat_id": str(chat_id),
            "message": message.model_dump(mode="json"),
        },
    )


async def publish_message_change(
    db: AsyncSession, chat_id: uuid.UUID, message: MessageRead, *, deleted: bool
) -> None:
    await _publish(
        await _chat_member_ids(db, chat_id),
        {
            "type": "message.deleted" if deleted else "message.edited",
            "chat_id": str(chat_id),
            "message": message.model_dump(mode="json"),
        },
    )


async def publish_typing(
    db: AsyncSession, chat_id: uuid.UUID, user_id: uuid.UUID, is_typing: bool
) -> None:
    recipients = [u for u in await _chat_member_ids(db, chat_id) if u != user_id]
    await _publish(
        recipients,
        {
            "type": "typing",
            "chat_id": str(chat_id),
            "user_id": str(user_id),
            "is_typing": is_typing,
        },
    )


async def publish_read(
    db: AsyncSession, chat_id: uuid.UUID, user_id: uuid.UUID, last_read_message_id: uuid.UUID
) -> None:
    recipients = [u for u in await _chat_member_ids(db, chat_id) if u != user_id]
    await _publish(
        recipients,
        {
            "type": "message.read",
            "chat_id": str(chat_id),
            "user_id": str(user_id),
            "last_read_message_id": str(last_read_message_id),
        },
    )


async def publish_presence(db: AsyncSession, user_id: uuid.UUID, status: str) -> None:
    recipients = [u for u in await _co_member_ids(db, user_id) if u != user_id]
    await _publish(recipients, {"type": "presence", "user_id": str(user_id), "status": status})


async def publish_post_new(db: AsyncSession, post: PostRead) -> None:
    """Notify the author's followers (and the author) of a new top-level post so
    open home timelines can surface it live."""
    author_id = post.author.id
    followers = list(
        (await db.scalars(select(Follow.follower_id).where(Follow.followee_id == author_id))).all()
    )
    await _publish(
        [*followers, author_id],
        {"type": "post.new", "post": post.model_dump(mode="json")},
    )
