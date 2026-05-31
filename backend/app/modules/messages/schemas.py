import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.schemas import UserPublic


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    reply_to_id: uuid.UUID | None = None


class MessageUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chat_id: uuid.UUID
    sender_id: uuid.UUID
    type: str
    content: str | None
    reply_to_id: uuid.UUID | None
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    sender: UserPublic


class MessagePage(BaseModel):
    messages: list[MessageRead]
    next_cursor: str | None = None
