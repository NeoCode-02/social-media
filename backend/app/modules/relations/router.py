import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_verified_user
from app.core.rate_limit import rate_limit
from app.modules.relations import service
from app.modules.users.models import User
from app.modules.users.schemas import UserPublic

router = APIRouter(prefix="/users", tags=["relations"])


@router.get("/me/blocks", response_model=list[UserPublic])
async def list_blocked(
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    return await service.list_blocked(db, user)


@router.get("/me/mutes", response_model=list[UserPublic])
async def list_muted(
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    return await service.list_muted(db, user)


@router.post(
    "/{user_id}/block",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limit(60, 60, "block")],
)
async def block_user(
    user_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.block(db, user, user_id)


@router.delete("/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    user_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.unblock(db, user, user_id)


@router.post(
    "/{user_id}/mute",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limit(60, 60, "mute")],
)
async def mute_user(
    user_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.mute(db, user, user_id)


@router.delete("/{user_id}/mute", status_code=status.HTTP_204_NO_CONTENT)
async def unmute_user(
    user_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.unmute(db, user, user_id)
