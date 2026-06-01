import uuid

import anyio
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_verified_user
from app.core.rate_limit import rate_limit
from app.core.storage import presigned_get_url
from app.modules.messages import service as msg_service
from app.modules.messages.models import Attachment
from app.modules.messages.schemas import AttachmentRead
from app.modules.posts import service
from app.modules.posts.schemas import PostCreate, PostPage, PostRead
from app.modules.realtime import events
from app.modules.users.models import User

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostPage)
async def home_timeline(
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
    before: uuid.UUID | None = Query(None),
) -> PostPage:
    return await service.home_timeline(db, user, limit, before)


@router.get("/global", response_model=PostPage)
async def global_timeline(
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
    before: uuid.UUID | None = Query(None),
) -> PostPage:
    return await service.global_timeline(db, user, limit, before)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PostRead,
    dependencies=[rate_limit(30, 60, "post_create")],
)
async def create_post(
    data: PostCreate,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> PostRead:
    post = await service.create_post(db, user, data)
    payload = (await service.build_posts(db, [post], user))[0]
    if post.parent_id is None:
        await events.publish_post_new(db, payload)
    return payload


@router.post(
    "/attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentRead,
    dependencies=[rate_limit(20, 60, "post_upload")],
)
async def upload_post_attachment(
    file: UploadFile = File(...),
    as_file: bool = Form(False),
    is_voice: bool = Form(False),
    duration_ms: int | None = Form(None),
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> AttachmentRead:
    data = await file.read()
    if len(data) > msg_service.MAX_ATTACHMENT_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File too large (max 100MB)")
    mime = file.content_type or "application/octet-stream"
    meta = await anyio.to_thread.run_sync(
        msg_service.process_blob, f"post/{user.id}", data, mime, as_file
    )
    attachment = await msg_service.record_attachment(
        db,
        None,
        user,
        file.filename or "file",
        mime,
        len(data),
        meta,
        as_file=as_file,
        is_voice=is_voice,
        duration_ms=duration_ms,
    )
    return AttachmentRead.model_validate(attachment)


@router.get("/attachments/{attachment_id}/download-url")
async def post_attachment_download_url(
    attachment_id: uuid.UUID,
    _: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    att = await db.get(Attachment, attachment_id)
    if att is None or att.post_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attachment not found")
    return {"url": presigned_get_url(att.storage_key, att.name)}


@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> PostRead:
    return await service.get_post(db, post_id, user)


@router.delete("/{post_id}", response_model=PostRead)
async def delete_post(
    post_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> PostRead:
    post = await service.delete_post(db, post_id, user)
    return (await service.build_posts(db, [post], user))[0]


@router.get("/{post_id}/replies", response_model=PostPage)
async def list_replies(
    post_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(30, ge=1, le=50),
    after: uuid.UUID | None = Query(None),
) -> PostPage:
    return await service.list_replies(db, post_id, user, limit, after)


@router.post("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_post(
    post_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.like(db, user, post_id)


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.unlike(db, user, post_id)


@router.post("/{post_id}/repost", status_code=status.HTTP_204_NO_CONTENT)
async def repost_post(
    post_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.repost(db, user, post_id)


@router.delete("/{post_id}/repost", status_code=status.HTTP_204_NO_CONTENT)
async def unrepost_post(
    post_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.unrepost(db, user, post_id)


# Profile feed — a single user's top-level posts + reposts.
user_router = APIRouter(prefix="/users", tags=["posts"])


@user_router.get("/{user_id}/posts", response_model=PostPage)
async def user_feed(
    user_id: uuid.UUID,
    user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
    before: uuid.UUID | None = Query(None),
) -> PostPage:
    return await service.user_feed(db, user_id, user, limit, before)
