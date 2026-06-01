import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.messages.schemas import AttachmentRead
from app.modules.users.schemas import UserPublic


class PostCreate(BaseModel):
    text: str | None = Field(default=None, max_length=2000)
    attachment_ids: list[uuid.UUID] | None = None
    parent_id: uuid.UUID | None = None  # set → this is a reply
    repost_of_id: uuid.UUID | None = None  # set → quote (with text) / repost

    @model_validator(mode="after")
    def require_body(self) -> "PostCreate":
        has_text = bool(self.text and self.text.strip())
        has_files = bool(self.attachment_ids)
        # A quote/repost may carry no body of its own; everything else needs one.
        if not has_text and not has_files and self.repost_of_id is None:
            raise ValueError("A post needs text or at least one attachment")
        return self


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author: UserPublic
    text: str | None
    parent_id: uuid.UUID | None
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    attachments: list[AttachmentRead] = []

    reply_count: int = 0
    repost_count: int = 0
    like_count: int = 0
    view_count: int = 0
    liked_by_me: bool = False
    reposted_by_me: bool = False

    # Embedded one level deep (their own repost_of / reply_to stay None).
    repost_of: "PostRead | None" = None
    reply_to: "PostRead | None" = None


class PostEdit(BaseModel):
    text: str | None = Field(default=None, max_length=2000)


class PostPage(BaseModel):
    posts: list[PostRead]
    next_cursor: str | None = None


class TrendingTag(BaseModel):
    tag: str
    count: int
