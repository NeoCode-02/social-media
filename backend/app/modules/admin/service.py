import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.sql import escape_like
from app.modules.admin.models import DISMISSED, OPEN, POST, RESOLVED, USER, Report
from app.modules.admin.schemas import (
    AdminStats,
    AdminUser,
    AdminUserPage,
    ReportPage,
    ReportRead,
)
from app.modules.posts import service as posts_service
from app.modules.posts.models import Post
from app.modules.users.models import User
from app.modules.users.schemas import UserPublic

MAX_PAGE = 50


def _today_start() -> datetime:
    """Midnight of the current day in the configured stats timezone, as UTC."""
    tz = ZoneInfo(settings.stats_timezone)
    local_midnight = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight.astimezone(UTC)


async def stats(db: AsyncSession) -> AdminStats:
    since = _today_start()

    async def count(stmt) -> int:
        return (await db.scalar(stmt)) or 0

    return AdminStats(
        total_users=await count(select(func.count()).select_from(User)),
        total_posts=await count(
            select(func.count()).select_from(Post).where(Post.deleted_at.is_(None))
        ),
        new_users_today=await count(
            select(func.count()).select_from(User).where(User.created_at >= since)
        ),
        new_posts_today=await count(
            select(func.count()).select_from(Post).where(
                Post.created_at >= since, Post.deleted_at.is_(None)
            )
        ),
        banned_users=await count(
            select(func.count()).select_from(User).where(User.is_banned.is_(True))
        ),
        private_accounts=await count(
            select(func.count()).select_from(User).where(User.is_private.is_(True))
        ),
        admins=await count(
            select(func.count()).select_from(User).where(User.is_admin.is_(True))
        ),
        open_reports=await count(
            select(func.count()).select_from(Report).where(Report.status == OPEN)
        ),
    )


async def list_users(
    db: AsyncSession, q: str | None, limit: int, offset: int
) -> AdminUserPage:
    limit = max(1, min(limit, MAX_PAGE))
    stmt = select(User)
    if q:
        like = f"%{escape_like(q)}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(like, escape="\\"),
                User.email.ilike(like, escape="\\"),
                User.display_name.ilike(like, escape="\\"),
            )
        )
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit + 1)
    rows = list((await db.scalars(stmt)).all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = str(offset + limit) if has_more else None
    return AdminUserPage(
        users=[AdminUser.model_validate(u) for u in rows], next_cursor=next_cursor
    )


async def _get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


async def set_banned(db: AsyncSession, admin: User, user_id: uuid.UUID, banned: bool) -> User:
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot ban yourself")
    user = await _get_user(db, user_id)
    user.is_banned = banned
    await db.commit()
    if banned:
        # Live-kick any open WebSocket for this user. Best-effort.
        from app.modules.realtime.router import mark_user_revoked

        await mark_user_revoked(user_id)
    return user


async def set_admin(db: AsyncSession, admin: User, user_id: uuid.UUID, value: bool) -> User:
    if user_id == admin.id and not value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot demote yourself")
    user = await _get_user(db, user_id)
    user.is_admin = value
    await db.commit()
    return user


async def verify_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await _get_user(db, user_id)
    user.email_verified = True
    await db.commit()
    return user


async def delete_user(db: AsyncSession, admin: User, user_id: uuid.UUID) -> None:
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot delete yourself")
    user = await _get_user(db, user_id)
    from app.modules.realtime.router import mark_user_revoked

    # Revoke the live session before deleting the row so the WS watcher
    # sees the flag first; even if the delete races, the flag is in Redis.
    await mark_user_revoked(user_id)
    await db.delete(user)
    await db.commit()


# --- reports ---------------------------------------------------------------


async def create_report(
    db: AsyncSession, reporter: User, target_type: str, target_id: uuid.UUID, reason: str
) -> None:
    if target_type == POST:
        if await db.get(Post, target_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
        report = Report(reporter_id=reporter.id, target_type=POST, post_id=target_id, reason=reason)
    elif target_type == USER:
        if target_id == reporter.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot report yourself")
        if await db.get(User, target_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        report = Report(reporter_id=reporter.id, target_type=USER, user_id=target_id, reason=reason)
    else:  # pragma: no cover - schema validates the pattern
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid target type")
    db.add(report)
    await db.commit()


async def list_reports(
    db: AsyncSession, admin: User, status_filter: str, limit: int, before: uuid.UUID | None
) -> ReportPage:
    limit = max(1, min(limit, MAX_PAGE))
    stmt = select(Report).where(Report.status == status_filter).order_by(Report.id.desc())
    if before is not None:
        stmt = stmt.where(Report.id < before)
    rows = list((await db.scalars(stmt.limit(limit + 1))).all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    cursor = str(rows[-1].id) if has_more and rows else None

    items: list[ReportRead] = []
    for r in rows:
        reporter = await db.get(User, r.reporter_id)
        if reporter is None:
            continue
        post_read = None
        if r.post_id is not None:
            post = await db.get(Post, r.post_id)
            if post is not None:
                post_read = (await posts_service.build_posts(db, [post], admin))[0]
        target_user = None
        if r.user_id is not None:
            tu = await db.get(User, r.user_id)
            target_user = UserPublic.model_validate(tu) if tu is not None else None
        items.append(
            ReportRead(
                id=r.id,
                target_type=r.target_type,
                reason=r.reason,
                status=r.status,
                created_at=r.created_at,
                reporter=UserPublic.model_validate(reporter),
                post=post_read,
                target_user=target_user,
            )
        )
    return ReportPage(reports=items, next_cursor=cursor)


async def resolve_report(
    db: AsyncSession, admin: User, report_id: uuid.UUID, dismissed: bool
) -> None:
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    report.status = DISMISSED if dismissed else RESOLVED
    report.resolved_by = admin.id
    report.resolved_at = datetime.now(UTC)
    await db.commit()
