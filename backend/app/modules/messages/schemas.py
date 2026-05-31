import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.users.schemas import UserPublic


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    thumbnail_url: str
    mime: str
    name: str
    size: int
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    as_file: bool = False
    is_voice: bool = False


class MessageCreate(BaseModel):
    content: str | None = Field(default=None, max_length=4000)
    reply_to_id: uuid.UUID | None = None
    attachment_ids: list[uuid.UUID] | None = None

    @model_validator(mode="after")
    def require_content_or_attachment(self) -> "MessageCreate":
        has_text = bool(self.content and self.content.strip())
        has_files = bool(self.attachment_ids)
        if not has_text and not has_files:
            raise ValueError("A message needs text or at least one attachment")
        return self


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
    attachments: list[AttachmentRead] = []


class MessagePage(BaseModel):
    messages: list[MessageRead]
    next_cursor: str | None = None
