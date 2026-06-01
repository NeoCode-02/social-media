import uuid
from datetime import datetime

from pydantic import BaseModel

from app.modules.users.schemas import UserPublic


class NotificationRead(BaseModel):
    id: uuid.UUID
    type: str
    actor: UserPublic
    post_id: uuid.UUID | None = None
    post_preview: str | None = None
    read: bool = False
    created_at: datetime


class NotificationPage(BaseModel):
    notifications: list[NotificationRead]
    next_cursor: str | None = None
    unread_count: int = 0


class MarkReadRequest(BaseModel):
    ids: list[uuid.UUID] | None = None  # None → mark all as read
