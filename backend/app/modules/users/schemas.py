import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: str | None = None


class UserProfile(UserPublic):
    """Full public profile for a user's page (heavier than the embedded
    UserPublic used inside every message/chat payload)."""

    bio: str | None = None
    location: str | None = None
    website: str | None = None
    created_at: datetime
    last_seen: datetime | None = None


class UserMe(UserProfile):
    email: str
    email_verified: bool


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=512)
    bio: str | None = Field(default=None, max_length=280)
    location: str | None = Field(default=None, max_length=64)
    website: str | None = Field(default=None, max_length=255)


class AvatarUploadRequest(BaseModel):
    content_type: str = Field(pattern=r"^image/(png|jpeg|jpg|webp|gif)$")


class AvatarUploadResponse(BaseModel):
    upload_url: str
    public_url: str
    key: str
