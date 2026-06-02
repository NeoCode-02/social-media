import uuid

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.chats.models import (
    CHAT_DM,
    CHAT_GROUP,
    ROLE_ADMIN,
    ROLE_MEMBER,
    ROLE_OWNER,
    Chat,
    ChatMember,
)
from app.modules.chats.schemas import ChatCreate, ChatMemberRead, ChatRead
from app.modules.messages.models import Message
from app.modules.messages.schemas import MessageRead
from app.modules.users.models import User

_chat_not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")


def _dm_key(a: uuid.UUID, b: uuid.UUID) -> str:
    lo, hi = sorted([str(a), str(b)])
    return f"{lo}:{hi}"


async def require_member(db: AsyncSession, chat_id: uuid.UUID, user_id: uuid.UUID) -> ChatMember:
    member = await db.get(ChatMember, {"chat_id": chat_id, "user_id": user_id})
    if member is None:
        raise _chat_not_found
    return member


async def create_chat(db: AsyncSession, current: User, data: ChatCreate) -> Chat:
    if data.type == CHAT_DM:
        return await _create_dm(db, current, data.user_id)
    return await _create_group(db, current, data.title, data.member_ids or [])


async def _create_dm(
    db: AsyncSession, current: User, other_id: uuid.UUID | None
) -> Chat:
    if other_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "user_id is required for a DM")
    if other_id == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot open a DM with yourself")
    other = await db.get(User, other_id)
    if other is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    key = _dm_key(current.id, other.id)
    existing = await db.scalar(select(Chat).where(Chat.dm_key == key))
    if existing is not None:
        return existing

    chat = Chat(type=CHAT_DM, created_by=current.id, dm_key=key)
    chat.members = [
        ChatMember(user_id=current.id, role=ROLE_MEMBER),
        ChatMember(user_id=other.id, role=ROLE_MEMBER),
    ]
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def _create_group(
    db: AsyncSession, current: User, title: str | None, member_ids: list[uuid.UUID]
) -> Chat:
    if not title:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "title is required for a group")
    ids = {uid for uid in member_ids if uid != current.id}
    members = [ChatMember(user_id=current.id, role=ROLE_OWNER)]
    if ids:
        found = set((await db.scalars(select(User.id).where(User.id.in_(ids)))).all())
        if ids - found:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "One or more users do not exist")
        members += [ChatMember(user_id=uid, role=ROLE_MEMBER) for uid in ids]

    chat = Chat(type=CHAT_GROUP, title=title, created_by=current.id)
    chat.members = members
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def _last_message(db: AsyncSession, chat_id: uuid.UUID) -> Message | None:
    return await db.scalar(
        select(Message)
        .where(Message.chat_id == chat_id, Message.deleted_at.is_(None))
        .order_by(Message.id.desc())  # UUIDv7 → newest
        .limit(1)
    )


async def _unread_count(
    db: AsyncSession, chat_id: uuid.UUID, user_id: uuid.UUID, last_read_id: uuid.UUID | None
) -> int:
    q = (
        select(func.count())
        .select_from(Message)
        .where(
            Message.chat_id == chat_id,
            Message.deleted_at.is_(None),
            Message.sender_id != user_id,  # don't count your own messages
        )
    )
    if last_read_id is not None:
        # UUIDv7 ids are monotonic: "unread" == ids after the last read one.
        q = q.where(Message.id > last_read_id)
    return await db.scalar(q) or 0


async def build_chat_read(
    db: AsyncSession,
    chat: Chat,
    member: ChatMember,
    *,
    last_message: Message | None = None,
    unread_count: int | None = None,
) -> ChatRead:
    # Use already-loaded members if available (selectinload), otherwise fetch.
    # In list_chats, they are pre-loaded.
    # We use a explicit check for the loaded state to avoid greenlet errors in Pydantic.
    inspect = sa.inspect(chat)
    if "members" in inspect.unloaded:
        members = (
            await db.scalars(
                select(ChatMember)
                .where(ChatMember.chat_id == chat.id)
                .options(selectinload(ChatMember.user))
            )
        ).all()
    else:
        members = chat.members
        # Even if members are loaded, their user relation might not be.
        for m in members:
            m_inspect = sa.inspect(m)
            if "user" in m_inspect.unloaded:
                await db.refresh(m, ["user"])

    last = last_message if last_message is not None else await _last_message(db, chat.id)
    if unread_count is not None:
        unread = unread_count
    else:
        unread = await _unread_count(db, chat.id, member.user_id, member.last_read_message_id)

    return ChatRead(
        id=chat.id,
        type=chat.type,
        title=chat.title,
        avatar_url=chat.avatar_url,
        created_at=chat.created_at,
        members=[ChatMemberRead.model_validate(m) for m in members],
        last_message=MessageRead.model_validate(last) if last is not None else None,
        unread_count=unread,
    )


async def list_chats(db: AsyncSession, user: User) -> list[ChatRead]:
    # 1. Fetch chats the user belongs to, pre-loading all members + users.
    # We join with ChatMember to filter by user.id.
    stmt = (
        select(Chat, ChatMember)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(ChatMember.user_id == user.id)
        .options(selectinload(Chat.members).selectinload(ChatMember.user))
    )
    rows = (await db.execute(stmt)).all()
    if not rows:
        return []

    chats = [r[0] for r in rows]
    my_memberships = {r[1].chat_id: r[1] for r in rows}
    chat_ids = list(my_memberships.keys())

    # 2. Fetch last messages for all these chats in one batch.
    # We use a subquery with ROW_NUMBER() to get the latest message per chat.
    msg_sub = (
        select(
            Message,
            func.row_number()
            .over(partition_by=Message.chat_id, order_by=Message.id.desc())
            .label("rn"),
        )
        .where(Message.chat_id.in_(chat_ids))
        .where(Message.deleted_at.is_(None))
    ).subquery()
    # selectinload(Message.sender) to avoid N+1 when validating MessageRead
    last_msgs_stmt = (
        select(Message)
        .where(Message.id.in_(select(msg_sub.c.id).where(msg_sub.c.rn == 1)))
        .options(selectinload(Message.sender))
    )
    last_msgs = (await db.scalars(last_msgs_stmt)).all()
    last_msg_map = {m.chat_id: m for m in last_msgs}

    # 3. Fetch unread counts in one batch.
    unread_stmt = (
        select(ChatMember.chat_id, func.count(Message.id))
        .join(Message, Message.chat_id == ChatMember.chat_id)
        .where(ChatMember.user_id == user.id)
        .where(ChatMember.chat_id.in_(chat_ids))
        .where(Message.sender_id != user.id)
        .where(Message.deleted_at.is_(None))
        .where(
            sa.or_(
                ChatMember.last_read_message_id.is_(None),
                Message.id > ChatMember.last_read_message_id,
            )
        )
        .group_by(ChatMember.chat_id)
    )
    unread_rows = (await db.execute(unread_stmt)).all()
    unread_map = {chat_id: count for chat_id, count in unread_rows}

    # 4. Build results.
    result: list[ChatRead] = []
    for chat in chats:
        member = my_memberships[chat.id]
        result.append(
            await build_chat_read(
                db,
                chat,
                member,
                last_message=last_msg_map.get(chat.id),
                unread_count=unread_map.get(chat.id, 0),
            )
        )

    # Most recent activity first.
    result.sort(
        key=lambda c: c.last_message.created_at if c.last_message else c.created_at,
        reverse=True,
    )
    return result


async def get_chat(db: AsyncSession, user: User, chat_id: uuid.UUID) -> ChatRead:
    member = await require_member(db, chat_id, user.id)
    chat = await db.get(Chat, chat_id)
    assert chat is not None
    return await build_chat_read(db, chat, member)


async def mark_read(
    db: AsyncSession, user: User, chat_id: uuid.UUID, message_id: uuid.UUID
) -> None:
    member = await require_member(db, chat_id, user.id)
    message = await db.get(Message, message_id)
    if message is None or message.chat_id != chat_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Message not in this chat")
    # Read pointer only moves forward (UUIDv7 ids are monotonic) — a stale/older
    # ack must not resurrect the unread badge.
    current = member.last_read_message_id
    if current is None or message_id > current:
        member.last_read_message_id = message_id
        await db.commit()


async def add_members(
    db: AsyncSession, user: User, chat_id: uuid.UUID, user_ids: list[uuid.UUID]
) -> ChatRead:
    member = await require_member(db, chat_id, user.id)
    chat = await db.get(Chat, chat_id)
    assert chat is not None
    if chat.type != CHAT_GROUP:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Can only add members to a group")
    if member.role not in (ROLE_OWNER, ROLE_ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only owners/admins can add members")

    existing = {m.user_id for m in chat.members}
    to_add = {uid for uid in user_ids if uid not in existing}
    if to_add:
        found = set((await db.scalars(select(User.id).where(User.id.in_(to_add)))).all())
        if to_add - found:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "One or more users do not exist")
        for uid in to_add:
            db.add(ChatMember(chat_id=chat_id, user_id=uid, role=ROLE_MEMBER))
        await db.commit()
        await db.refresh(chat)
    return await build_chat_read(db, chat, member)


async def leave_chat(db: AsyncSession, user: User, chat_id: uuid.UUID) -> None:
    member = await require_member(db, chat_id, user.id)
    await db.delete(member)
    await db.commit()
