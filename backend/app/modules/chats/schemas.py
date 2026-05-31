import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.messages.schemas import MessageRead
from app.modules.users.schemas import UserPublic


class ChatCreate(BaseModel):
    type: Literal["dm", "group"]
    # DM: the other participant.
    user_id: uuid.UUID | None = None
    # Group:
    title: str | None = Field(default=None, max_length=128)
    member_ids: list[uuid.UUID] | None = None


class ChatMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    last_read_message_id: uuid.UUID | None
    user: UserPublic


class ChatRead(BaseModel):
    id: uuid.UUID
    type: str
    title: str | None
    avatar_url: str | None
    created_at: datetime
    members: list[ChatMemberRead]
    last_message: MessageRead | None = None
    unread_count: int = 0


class MarkReadRequest(BaseModel):
    last_read_message_id: uuid.UUID


class AddMembersRequest(BaseModel):
    user_ids: list[uuid.UUID] = Field(min_length=1)
