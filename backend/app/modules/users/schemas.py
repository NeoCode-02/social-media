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
    is_private: bool = False

    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_following: bool = False  # requester has an accepted follow of this user
    follow_state: str = "none"  # "none" | "pending" | "accepted"
    can_view_posts: bool = True  # False → private + requester not an accepted follower


class UserMe(UserProfile):
    email: str
    email_verified: bool
    pending_requests: int = 0  # follow requests awaiting my approval


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=512)
    bio: str | None = Field(default=None, max_length=280)
    location: str | None = Field(default=None, max_length=64)
    website: str | None = Field(default=None, max_length=255)
    is_private: bool | None = None
