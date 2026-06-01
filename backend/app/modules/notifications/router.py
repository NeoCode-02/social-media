import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_verified_user
from app.modules.notifications import service
from app.modules.notifications.schemas import MarkReadRequest, NotificationPage
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationPage)
async def list_notifications(
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
    before: uuid.UUID | None = Query(None),
) -> NotificationPage:
    return await service.list_notifications(db, user, limit, before)


@router.get("/unread-count")
async def unread_count(
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return {"count": await service.unread_count(db, user.id)}


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    data: MarkReadRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.mark_read(db, user, data.ids)
