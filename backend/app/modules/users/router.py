import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.storage import presigned_put_url, public_url
from app.modules.users.models import User
from app.modules.users.schemas import (
    AvatarUploadRequest,
    AvatarUploadResponse,
    UserMe,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])

_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}


@router.get("/me", response_model=UserMe)
async def get_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserMe)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/me/avatar-url", response_model=AvatarUploadResponse)
async def create_avatar_upload_url(
    data: AvatarUploadRequest,
    user: User = Depends(get_current_user),
) -> AvatarUploadResponse:
    ext = _EXT[data.content_type]
    key = f"avatars/{user.id}/{uuid.uuid4().hex}.{ext}"
    return AvatarUploadResponse(
        upload_url=presigned_put_url(key, data.content_type),
        public_url=public_url(key),
        key=key,
    )
