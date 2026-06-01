import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.follows.models import Follow
from app.modules.relations.models import Block, Mute
from app.modules.users.models import User


async def block(db: AsyncSession, blocker: User, blocked_id: uuid.UUID) -> None:
    if blocker.id == blocked_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot block yourself")
    if await db.get(User, blocked_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if await db.get(Block, {"blocker_id": blocker.id, "blocked_id": blocked_id}) is None:
        db.add(Block(blocker_id=blocker.id, blocked_id=blocked_id))
    # Blocking severs any follow relationship in both directions.
    await db.execute(
        delete(Follow).where(
            or_(
                (Follow.follower_id == blocker.id) & (Follow.followee_id == blocked_id),
                (Follow.follower_id == blocked_id) & (Follow.followee_id == blocker.id),
            )
        )
    )
    await db.commit()


async def unblock(db: AsyncSession, blocker: User, blocked_id: uuid.UUID) -> None:
    row = await db.get(Block, {"blocker_id": blocker.id, "blocked_id": blocked_id})
    if row is not None:
        await db.delete(row)
        await db.commit()


async def mute(db: AsyncSession, muter: User, muted_id: uuid.UUID) -> None:
    if muter.id == muted_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot mute yourself")
    if await db.get(User, muted_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if await db.get(Mute, {"muter_id": muter.id, "muted_id": muted_id}) is None:
        db.add(Mute(muter_id=muter.id, muted_id=muted_id))
        await db.commit()


async def unmute(db: AsyncSession, muter: User, muted_id: uuid.UUID) -> None:
    row = await db.get(Mute, {"muter_id": muter.id, "muted_id": muted_id})
    if row is not None:
        await db.delete(row)
        await db.commit()


async def is_blocking(db: AsyncSession, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> bool:
    return (
        await db.get(Block, {"blocker_id": blocker_id, "blocked_id": blocked_id})
    ) is not None


async def is_muting(db: AsyncSession, muter_id: uuid.UUID, muted_id: uuid.UUID) -> bool:
    return (await db.get(Mute, {"muter_id": muter_id, "muted_id": muted_id})) is not None


async def blocked_pair(db: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> bool:
    """True if either user has blocked the other."""
    if a == b:
        return False
    row = await db.scalar(
        select(Block.blocker_id).where(
            or_(
                (Block.blocker_id == a) & (Block.blocked_id == b),
                (Block.blocker_id == b) & (Block.blocked_id == a),
            )
        )
    )
    return row is not None


async def blocked_ids(db: AsyncSession, viewer_id: uuid.UUID) -> set[uuid.UUID]:
    """Everyone in a mutual block with viewer (either direction)."""
    out = await db.scalars(
        select(Block.blocked_id).where(Block.blocker_id == viewer_id)
    )
    inc = await db.scalars(
        select(Block.blocker_id).where(Block.blocked_id == viewer_id)
    )
    return set(out.all()) | set(inc.all())


async def feed_excluded_ids(db: AsyncSession, viewer_id: uuid.UUID) -> set[uuid.UUID]:
    """Authors to hide from viewer's feeds: blocked (either way) + muted."""
    muted = await db.scalars(select(Mute.muted_id).where(Mute.muter_id == viewer_id))
    return (await blocked_ids(db, viewer_id)) | set(muted.all())


async def list_blocked(db: AsyncSession, viewer: User) -> list[User]:
    sub = select(Block.blocked_id).where(Block.blocker_id == viewer.id)
    rows = await db.scalars(select(User).where(User.id.in_(sub)).order_by(User.username))
    return list(rows.all())


async def list_muted(db: AsyncSession, viewer: User) -> list[User]:
    sub = select(Mute.muted_id).where(Mute.muter_id == viewer.id)
    rows = await db.scalars(select(User).where(User.id.in_(sub)).order_by(User.username))
    return list(rows.all())
