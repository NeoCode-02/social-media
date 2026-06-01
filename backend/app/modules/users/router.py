import asyncio
import uuid

import anyio
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user, get_current_verified_user
from app.core.images import make_thumbnail
from app.core.rate_limit import rate_limit
from app.core.storage import delete_object, public_url, put_object
from app.modules.follows import service as follows_service
from app.modules.follows.models import ACCEPTED
from app.modules.posts import service as posts_service
from app.modules.users.models import User
from app.modules.users.schemas import (
    UserMe,
    UserProfile,
    UserPublic,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])

MAX_AVATAR_BYTES = 25 * 1024 * 1024


async def _social(db: AsyncSession, target: User, viewer: User) -> dict[str, int | bool | str]:
    """Counts + the viewer's follow relationship & post-visibility to target."""
    is_self = viewer.id == target.id
    followers, following, posts, state = await asyncio.gather(
        follows_service.followers_count(db, target.id),
        follows_service.following_count(db, target.id),
        posts_service.posts_count(db, target.id),
        (
            asyncio.sleep(0, result="none")
            if is_self
            else follows_service.follow_state(db, viewer.id, target.id)
        ),
    )
    is_following = state == ACCEPTED
    return {
        "followers_count": followers,
        "following_count": following,
        "posts_count": posts,
        "is_following": is_following,
        "follow_state": state,
        "can_view_posts": (not target.is_private) or is_self or is_following,
    }

_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}


@router.get(
    "/search",
    response_model=list[UserPublic],
    dependencies=[rate_limit(40, 60, "search")],
)
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
async def get_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserMe:
    social = await _social(db, user, user)
    social["pending_requests"] = await follows_service.pending_count(db, user.id)
    return UserMe.model_validate(user).model_copy(update=social)


async def _profile(db: AsyncSession, user: User, viewer: User) -> UserProfile:
    social = await _social(db, user, viewer)
    profile = UserProfile.model_validate(user).model_copy(update=social)
    # Hide rich details from outsiders of a private account.
    if not social["can_view_posts"]:
        profile = profile.model_copy(
            update={"bio": None, "location": None, "website": None, "last_seen": None}
        )
    return profile


@router.get("/by-username/{username}", response_model=UserProfile)
async def get_user_by_username(
    username: str,
    viewer: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    user = (
        await db.scalars(select(User).where(func.lower(User.username) == username.lower()))
    ).first()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return await _profile(db, user, viewer)


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: uuid.UUID,
    viewer: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return await _profile(db, user, viewer)


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



def _process_avatar(data: bytes, old_url: str | None) -> str:
    """Thumbnailing + cleanup of old avatar (if applicable)."""
    thumb = make_thumbnail(data)
    if not thumb:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid image data")

    # Cleanup old avatar if it's in our S3 bucket.
    if old_url:
        prefix = f"{settings.s3_public_url}/{settings.s3_bucket}/"
        if old_url.startswith(prefix):
            try:
                delete_object(old_url.removeprefix(prefix))
            except Exception:
                pass  # best effort cleanup

    key = f"avatars/{uuid.uuid4().hex}.jpg"
    put_object(key, thumb, "image/jpeg")
    return public_url(key)


@router.post("/me/avatar", response_model=UserMe)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserMe:
    if file.content_type not in _EXT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported image type")
    data = await file.read()
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Image too large (max 25MB)")

    new_url = await anyio.to_thread.run_sync(_process_avatar, data, user.avatar_url)
    user.avatar_url = new_url
    await db.commit()
    await db.refresh(user)
    return UserMe.model_validate(user).model_copy(update=await _social(db, user, user))
