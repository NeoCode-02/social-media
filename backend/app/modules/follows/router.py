import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_verified_user
from app.core.rate_limit import rate_limit
from app.modules.follows import service
from app.modules.users.models import User
from app.modules.users.schemas import UserPublic

router = APIRouter(prefix="/users", tags=["follows"])


@router.post(
    "/{user_id}/follow",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limit(60, 60, "follow")],
)
async def follow_user(
    user_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.follow(db, user, user_id)


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.unfollow(db, user, user_id)


@router.get("/{user_id}/followers", response_model=list[UserPublic])
async def list_followers(
    user_id: uuid.UUID,
    _: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    return await service.list_followers(db, user_id)


@router.get("/{user_id}/following", response_model=list[UserPublic])
async def list_following(
    user_id: uuid.UUID,
    _: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    return await service.list_following(db, user_id)
