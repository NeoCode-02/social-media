import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: str | None = None


class UserMe(UserPublic):
    email: str
    email_verified: bool
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=512)


class AvatarUploadRequest(BaseModel):
    content_type: str = Field(pattern=r"^image/(png|jpeg|jpg|webp|gif)$")


class AvatarUploadResponse(BaseModel):
    upload_url: str
    public_url: str
    key: str
