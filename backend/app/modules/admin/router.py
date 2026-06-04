import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_admin, get_current_verified_user
from app.core.rate_limit import rate_limit
from app.modules.admin import service
from app.modules.admin.schemas import (
    AdminStats,
    AdminUser,
    AdminUserPage,
    ReportCreate,
    ReportPage,
)
from app.modules.posts import service as posts_service
from app.modules.posts.schemas import PostPage, PostRead
from app.modules.users.models import User

# --- moderator surface (all behind get_current_admin) ----------------------

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
async def get_stats(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminStats:
    return await service.stats(db)


@router.get("/users", response_model=AdminUserPage)
async def list_users(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None, max_length=64),
    limit: int = Query(25, ge=1, le=50),
    offset: int = Query(0, ge=0),
) -> AdminUserPage:
    return await service.list_users(db, q, limit, offset)


@router.post("/users/{user_id}/ban", response_model=AdminUser)
async def ban_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await service.set_banned(db, admin, user_id, True)


@router.post("/users/{user_id}/unban", response_model=AdminUser)
async def unban_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await service.set_banned(db, admin, user_id, False)


@router.post("/users/{user_id}/promote", response_model=AdminUser)
async def promote_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await service.set_admin(db, admin, user_id, True)


@router.post("/users/{user_id}/demote", response_model=AdminUser)
async def demote_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await service.set_admin(db, admin, user_id, False)


@router.post("/users/{user_id}/verify", response_model=AdminUser)
async def verify_user(
    user_id: uuid.UUID,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await service.verify_user(db, user_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.delete_user(db, admin, user_id)


@router.get("/posts", response_model=PostPage)
async def list_posts(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None, max_length=100),
    limit: int = Query(25, ge=1, le=50),
    before: uuid.UUID | None = Query(None),
) -> PostPage:
    return await posts_service.admin_list_posts(db, admin, q, limit, before)


@router.delete("/posts/{post_id}", response_model=PostRead)
async def delete_post(
    post_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> PostRead:
    post = await posts_service.admin_delete_post(db, post_id)
    return (await posts_service.build_posts(db, [post], admin, enforce_visibility=False))[0]


@router.get("/reports", response_model=ReportPage)
async def list_reports(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    status_filter: str = Query("open", alias="status", pattern="^(open|resolved|dismissed)$"),
    limit: int = Query(25, ge=1, le=50),
    before: uuid.UUID | None = Query(None),
) -> ReportPage:
    return await service.list_reports(db, admin, status_filter, limit, before)


@router.post("/reports/{report_id}/resolve", status_code=status.HTTP_204_NO_CONTENT)
async def resolve_report(
    report_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.resolve_report(db, admin, report_id, dismissed=False)


@router.post("/reports/{report_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_report(
    report_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.resolve_report(db, admin, report_id, dismissed=True)


# --- user-facing reporting -------------------------------------------------

reports_router = APIRouter(prefix="/reports", tags=["reports"])


@reports_router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limit(20, 60, "report")],
)
async def create_report(
    data: ReportCreate,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.create_report(db, user, data.target_type, data.target_id, data.reason)
