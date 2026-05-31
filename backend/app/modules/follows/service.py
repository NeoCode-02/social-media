import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.follows.models import Follow
from app.modules.users.models import User


async def follow(db: AsyncSession, follower: User, followee_id: uuid.UUID) -> None:
    if follower.id == followee_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot follow yourself")
    if await db.get(User, followee_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    existing = await db.get(Follow, {"follower_id": follower.id, "followee_id": followee_id})
    if existing is None:
        db.add(Follow(follower_id=follower.id, followee_id=followee_id))
        await db.commit()


async def unfollow(db: AsyncSession, follower: User, followee_id: uuid.UUID) -> None:
    existing = await db.get(Follow, {"follower_id": follower.id, "followee_id": followee_id})
    if existing is not None:
        await db.delete(existing)
        await db.commit()


async def is_following(
    db: AsyncSession, follower_id: uuid.UUID, followee_id: uuid.UUID
) -> bool:
    return (
        await db.get(Follow, {"follower_id": follower_id, "followee_id": followee_id})
    ) is not None


async def followers_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    q = select(func.count()).select_from(Follow).where(Follow.followee_id == user_id)
    return (await db.scalar(q)) or 0


async def following_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    q = select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
    return (await db.scalar(q)) or 0


async def list_followers(db: AsyncSession, user_id: uuid.UUID) -> list[User]:
    sub = select(Follow.follower_id).where(Follow.followee_id == user_id)
    q = select(User).where(User.id.in_(sub)).order_by(User.username)
    return list((await db.scalars(q)).all())


async def list_following(db: AsyncSession, user_id: uuid.UUID) -> list[User]:
    sub = select(Follow.followee_id).where(Follow.follower_id == user_id)
    q = select(User).where(User.id.in_(sub)).order_by(User.username)
    return list((await db.scalars(q)).all())
