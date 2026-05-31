import uuid

import anyio
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_current_verified_user
from app.core.storage import presigned_put_url, public_url, put_object
from app.modules.users.models import User
from app.modules.users.schemas import (
    AvatarUploadRequest,
    AvatarUploadResponse,
    UserMe,
    UserPublic,
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


@router.get("/search", response_model=list[UserPublic])
async def search_users(
    q: str = Query(min_length=1, max_length=32),
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    rows = await db.scalars(
        select(User)
        .where(User.id != user.id, User.username.ilike(f"%{q}%"))
        .order_by(User.username)
        .limit(10)
    )
    return list(rows.all())


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


@router.post("/me/avatar", response_model=UserMe)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if file.content_type not in _EXT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported image type")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Image too large (max 5MB)")
    key = f"avatars/{user.id}/{uuid.uuid4().hex}.{_EXT[file.content_type]}"
    await anyio.to_thread.run_sync(put_object, key, data, file.content_type)
    user.avatar_url = public_url(key)
    await db.commit()
    await db.refresh(user)
    return user
