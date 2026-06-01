import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import MENTION, Notification
from app.modules.notifications.schemas import NotificationPage, NotificationRead
from app.modules.posts.models import Post
from app.modules.posts.text import extract_mentions
from app.modules.realtime import events
from app.modules.users.models import User
from app.modules.users.schemas import UserPublic

MAX_PAGE = 50


async def _preview(db: AsyncSession, post_id: uuid.UUID | None) -> str | None:
    if post_id is None:
        return None
    text = await db.scalar(select(Post.text).where(Post.id == post_id))
    if not text:
        return None
    return text[:80]


async def _to_read(db: AsyncSession, n: Notification, actor: User) -> NotificationRead:
    return NotificationRead(
        id=n.id,
        type=n.type,
        actor=UserPublic.model_validate(actor),
        post_id=n.post_id,
        post_preview=await _preview(db, n.post_id),
        read=n.read_at is not None,
        created_at=n.created_at,
    )


async def notify(
    db: AsyncSession,
    *,
    recipient_id: uuid.UUID,
    actor_id: uuid.UUID,
    type: str,
    post_id: uuid.UUID | None = None,
    unique: bool = False,
) -> None:
    """Create a notification (skipping self-actions) and push it in realtime."""
    if recipient_id == actor_id:
        return
    if unique:
        post_match = (
            Notification.post_id.is_(None)
            if post_id is None
            else Notification.post_id == post_id
        )
        exists = await db.scalar(
            select(Notification.id).where(
                Notification.recipient_id == recipient_id,
                Notification.actor_id == actor_id,
                Notification.type == type,
                post_match,
            )
        )
        if exists is not None:
            return

    n = Notification(
        recipient_id=recipient_id, actor_id=actor_id, type=type, post_id=post_id
    )
    db.add(n)
    await db.commit()
    await db.refresh(n)

    actor = await db.get(User, actor_id)
    if actor is None:
        return
    payload = await _to_read(db, n, actor)
    await events._publish(
        [recipient_id],
        {"type": "notification.new", "notification": payload.model_dump(mode="json")},
    )


async def notify_mentions(
    db: AsyncSession, text: str | None, actor: User, post_id: uuid.UUID
) -> None:
    """Notify every mentioned (existing) user, excluding the author."""
    usernames = extract_mentions(text)
    if not usernames:
        return
    rows = (
        await db.scalars(
            select(User.id).where(func.lower(User.username).in_(usernames))
        )
    ).all()
    for uid in rows:
        await notify(
            db,
            recipient_id=uid,
            actor_id=actor.id,
            type=MENTION,
            post_id=post_id,
            unique=True,
        )


async def unread_count(db: AsyncSession, recipient_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.read_at.is_(None),
            )
        )
    ) or 0


async def list_notifications(
    db: AsyncSession, recipient: User, limit: int, before: uuid.UUID | None
) -> NotificationPage:
    limit = max(1, min(limit, MAX_PAGE))
    q = (
        select(Notification)
        .where(Notification.recipient_id == recipient.id)
        .order_by(Notification.id.desc())
        .limit(limit + 1)
    )
    if before is not None:
        q = q.where(Notification.id < before)
    rows = list((await db.scalars(q)).all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    cursor = str(rows[-1].id) if has_more and rows else None

    # Batch-load actors.
    actor_ids = {n.actor_id for n in rows}
    actors = {
        u.id: u
        for u in (await db.scalars(select(User).where(User.id.in_(actor_ids)))).all()
    }
    items = [await _to_read(db, n, actors[n.actor_id]) for n in rows if n.actor_id in actors]
    return NotificationPage(
        notifications=items,
        next_cursor=cursor,
        unread_count=await unread_count(db, recipient.id),
    )


async def mark_read(
    db: AsyncSession, recipient: User, ids: list[uuid.UUID] | None
) -> None:
    stmt = (
        update(Notification)
        .where(Notification.recipient_id == recipient.id, Notification.read_at.is_(None))
        .values(read_at=func.now())
    )
    if ids:
        stmt = stmt.where(Notification.id.in_(ids))
    await db.execute(stmt)
    await db.commit()
