import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.posts.schemas import PostRead
from app.modules.users.schemas import UserPublic


class AdminStats(BaseModel):
    total_users: int
    total_posts: int
    new_users_today: int
    new_posts_today: int
    banned_users: int
    private_accounts: int
    admins: int
    open_reports: int


class AdminUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    email: str
    avatar_url: str | None = None
    email_verified: bool
    is_admin: bool
    is_banned: bool
    is_private: bool
    created_at: datetime


class AdminUserPage(BaseModel):
    users: list[AdminUser]
    next_cursor: str | None = None


class ReportCreate(BaseModel):
    target_type: str = Field(pattern="^(post|user)$")
    target_id: uuid.UUID
    reason: str = Field(default="", max_length=280)


class ReportRead(BaseModel):
    id: uuid.UUID
    target_type: str
    reason: str
    status: str
    created_at: datetime
    reporter: UserPublic
    post: PostRead | None = None
    target_user: UserPublic | None = None


class ReportPage(BaseModel):
    reports: list[ReportRead]
    next_cursor: str | None = None
