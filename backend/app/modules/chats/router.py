import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_verified_user
from app.modules.chats import service
from app.modules.chats.schemas import (
    AddMembersRequest,
    ChatCreate,
    ChatRead,
    MarkReadRequest,
)
from app.modules.messages import service as msg_service
from app.modules.messages.schemas import MessageCreate, MessagePage, MessageRead
from app.modules.users.models import User

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatRead])
async def list_my_chats(
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatRead]:
    return await service.list_chats(db, user)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ChatRead)
async def create_chat(
    data: ChatCreate,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> ChatRead:
    chat = await service.create_chat(db, user, data)
    member = await service.require_member(db, chat.id, user.id)
    return await service.build_chat_read(db, chat, member)


@router.get("/{chat_id}", response_model=ChatRead)
async def get_chat(
    chat_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> ChatRead:
    return await service.get_chat(db, user, chat_id)


@router.post("/{chat_id}/members", response_model=ChatRead)
async def add_members(
    chat_id: uuid.UUID,
    data: AddMembersRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> ChatRead:
    return await service.add_members(db, user, chat_id, data.user_ids)


@router.delete("/{chat_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_chat(
    chat_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.leave_chat(db, user, chat_id)


@router.post("/{chat_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    chat_id: uuid.UUID,
    data: MarkReadRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.mark_read(db, user, chat_id, data.last_read_message_id)


@router.get("/{chat_id}/messages", response_model=MessagePage)
async def list_messages(
    chat_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(30, ge=1, le=50),
    before: uuid.UUID | None = Query(None),
) -> MessagePage:
    await service.require_member(db, chat_id, user.id)
    return await msg_service.list_messages(db, chat_id, limit, before)


@router.post(
    "/{chat_id}/messages",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageRead,
)
async def send_message(
    chat_id: uuid.UUID,
    data: MessageCreate,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    await service.require_member(db, chat_id, user.id)
    message = await msg_service.create_message(db, chat_id, user, data)
    return MessageRead.model_validate(message)
