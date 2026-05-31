import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_verified_user
from app.modules.messages import service
from app.modules.messages.schemas import MessageRead, MessageUpdate
from app.modules.realtime import events
from app.modules.users.models import User

router = APIRouter(prefix="/messages", tags=["messages"])


@router.patch("/{message_id}", response_model=MessageRead)
async def edit_message(
    message_id: uuid.UUID,
    data: MessageUpdate,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    message = await service.edit_message(db, message_id, user, data.content)
    payload = MessageRead.model_validate(message)
    await events.publish_message_change(db, message.chat_id, payload, deleted=False)
    return payload


@router.delete("/{message_id}", response_model=MessageRead)
async def delete_message(
    message_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    message = await service.delete_message(db, message_id, user)
    payload = MessageRead.model_validate(message)
    await events.publish_message_change(db, message.chat_id, payload, deleted=True)
    return payload
