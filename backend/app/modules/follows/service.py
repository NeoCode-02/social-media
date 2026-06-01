import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.follows.models import ACCEPTED, PENDING, Follow
from app.modules.relations import service as relations
from app.modules.users.models import User


async def follow(db: AsyncSession, follower: User, followee_id: uuid.UUID) -> str:
    """Follow (public) or request to follow (private). Returns the resulting status."""
    if follower.id == followee_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot follow yourself")
    target = await db.get(User, followee_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if await relations.blocked_pair(db, follower.id, followee_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Unavailable")
    existing = await db.get(Follow, {"follower_id": follower.id, "followee_id": followee_id})
    if existing is not None:
        return existing.status
    new_status = PENDING if target.is_private else ACCEPTED
    db.add(Follow(follower_id=follower.id, followee_id=followee_id, status=new_status))
    await db.commit()
    return new_status


async def unfollow(db: AsyncSession, follower: User, followee_id: uuid.UUID) -> None:
    """Unfollow, or cancel a still-pending request."""
    existing = await db.get(Follow, {"follower_id": follower.id, "followee_id": followee_id})
    if existing is not None:
        await db.delete(existing)
        await db.commit()


async def accept_request(db: AsyncSession, owner: User, follower_id: uuid.UUID) -> None:
    """Owner accepts a pending follow request from follower_id."""
    row = await db.get(Follow, {"follower_id": follower_id, "followee_id": owner.id})
    if row is None or row.status != PENDING:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No pending request")
    row.status = ACCEPTED
    await db.commit()


async def reject_request(db: AsyncSession, owner: User, follower_id: uuid.UUID) -> None:
    """Owner rejects (deletes) a pending follow request from follower_id."""
    row = await db.get(Follow, {"follower_id": follower_id, "followee_id": owner.id})
    if row is None or row.status != PENDING:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No pending request")
    await db.delete(row)
    await db.commit()


async def follow_state(
    db: AsyncSession, follower_id: uuid.UUID, followee_id: uuid.UUID
) -> str:
    """'none' | 'pending' | 'accepted' for follower → followee."""
    row = await db.get(Follow, {"follower_id": follower_id, "followee_id": followee_id})
    return row.status if row is not None else "none"


async def is_following(
    db: AsyncSession, follower_id: uuid.UUID, followee_id: uuid.UUID
) -> bool:
    """True only for an accepted follow."""
    row = await db.get(Follow, {"follower_id": follower_id, "followee_id": followee_id})
    return row is not None and row.status == ACCEPTED


async def followers_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    q = (
        select(func.count())
        .select_from(Follow)
        .where(Follow.followee_id == user_id, Follow.status == ACCEPTED)
    )
    return (await db.scalar(q)) or 0


async def following_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    q = (
        select(func.count())
        .select_from(Follow)
        .where(Follow.follower_id == user_id, Follow.status == ACCEPTED)
    )
    return (await db.scalar(q)) or 0


async def pending_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Number of follow requests awaiting this user's approval."""
    q = (
        select(func.count())
        .select_from(Follow)
        .where(Follow.followee_id == user_id, Follow.status == PENDING)
    )
    return (await db.scalar(q)) or 0


async def list_followers(db: AsyncSession, user_id: uuid.UUID) -> list[User]:
    sub = select(Follow.follower_id).where(
        Follow.followee_id == user_id, Follow.status == ACCEPTED
    )
    q = select(User).where(User.id.in_(sub)).order_by(User.username)
    return list((await db.scalars(q)).all())


async def list_following(db: AsyncSession, user_id: uuid.UUID) -> list[User]:
    sub = select(Follow.followee_id).where(
        Follow.follower_id == user_id, Follow.status == ACCEPTED
    )
    q = select(User).where(User.id.in_(sub)).order_by(User.username)
    return list((await db.scalars(q)).all())


async def list_requests(db: AsyncSession, owner: User) -> list[User]:
    """Users with a pending follow request to owner (the request inbox)."""
    sub = select(Follow.follower_id).where(
        Follow.followee_id == owner.id, Follow.status == PENDING
    )
    q = select(User).where(User.id.in_(sub)).order_by(User.username)
    return list((await db.scalars(q)).all())
