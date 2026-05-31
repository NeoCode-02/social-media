import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.follows.models import Follow
from app.modules.messages.models import Attachment
from app.modules.posts.models import Like, Post
from app.modules.posts.schemas import PostCreate, PostPage, PostRead
from app.modules.users.models import User

MAX_PAGE = 50


def _now() -> datetime:
    return datetime.now(UTC)


async def _get_loaded(db: AsyncSession, post_id: uuid.UUID) -> Post | None:
    """Fetch a post with its author + attachments eagerly loaded (selectin)."""
    return (await db.scalars(select(Post).where(Post.id == post_id))).first()


async def _alive(db: AsyncSession, post_id: uuid.UUID) -> Post:
    post = await _get_loaded(db, post_id)
    if post is None or post.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return post


async def create_post(db: AsyncSession, author: User, data: PostCreate) -> Post:
    if data.parent_id is not None:
        await _alive(db, data.parent_id)
    if data.repost_of_id is not None:
        await _alive(db, data.repost_of_id)

    attachments: list[Attachment] = []
    if data.attachment_ids:
        for aid in data.attachment_ids:
            att = await db.get(Attachment, aid)
            if (
                att is None
                or att.uploader_id != author.id
                or att.post_id is not None
                or att.chat_id is not None
                or att.message_id is not None
            ):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid attachment")
            attachments.append(att)

    post = Post(
        author_id=author.id,
        text=data.text,
        parent_id=data.parent_id,
        repost_of_id=data.repost_of_id,
    )
    db.add(post)
    await db.flush()
    for att in attachments:
        att.post_id = post.id
    await db.commit()
    loaded = await _get_loaded(db, post.id)
    assert loaded is not None
    return loaded


async def delete_post(db: AsyncSession, post_id: uuid.UUID, user: User) -> Post:
    post = await db.get(Post, post_id)
    if post is None or post.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your post")
    post.deleted_at = _now()
    post.text = None
    await db.commit()
    loaded = await _get_loaded(db, post.id)
    assert loaded is not None
    return loaded


async def like(db: AsyncSession, user: User, post_id: uuid.UUID) -> None:
    await _alive(db, post_id)
    existing = await db.get(Like, {"user_id": user.id, "post_id": post_id})
    if existing is None:
        db.add(Like(user_id=user.id, post_id=post_id))
        await db.commit()


async def unlike(db: AsyncSession, user: User, post_id: uuid.UUID) -> None:
    existing = await db.get(Like, {"user_id": user.id, "post_id": post_id})
    if existing is not None:
        await db.delete(existing)
        await db.commit()


async def _my_repost(db: AsyncSession, user_id: uuid.UUID, post_id: uuid.UUID) -> Post | None:
    return (
        await db.scalars(
            select(Post).where(
                Post.author_id == user_id,
                Post.repost_of_id == post_id,
                Post.text.is_(None),
                Post.deleted_at.is_(None),
            )
        )
    ).first()


async def repost(db: AsyncSession, user: User, post_id: uuid.UUID) -> Post:
    await _alive(db, post_id)
    existing = await _my_repost(db, user.id, post_id)
    if existing is not None:
        return existing
    post = Post(author_id=user.id, repost_of_id=post_id, text=None)
    db.add(post)
    await db.commit()
    loaded = await _get_loaded(db, post.id)
    assert loaded is not None
    return loaded


async def unrepost(db: AsyncSession, user: User, post_id: uuid.UUID) -> None:
    existing = await _my_repost(db, user.id, post_id)
    if existing is not None:
        await db.delete(existing)
        await db.commit()


# ---- read side -------------------------------------------------------------


async def _counts(
    db: AsyncSession, ids: list[uuid.UUID]
) -> tuple[dict[uuid.UUID, int], dict[uuid.UUID, int], dict[uuid.UUID, int]]:
    """Likes / replies / reposts counts for a batch of post ids (drift-free)."""
    empty: dict[uuid.UUID, int] = {}
    if not ids:
        return empty, dict(empty), dict(empty)
    like_rows = (
        await db.execute(
            select(Like.post_id, func.count()).where(Like.post_id.in_(ids)).group_by(Like.post_id)
        )
    ).all()
    reply_rows = (
        await db.execute(
            select(Post.parent_id, func.count())
            .where(Post.parent_id.in_(ids), Post.deleted_at.is_(None))
            .group_by(Post.parent_id)
        )
    ).all()
    repost_rows = (
        await db.execute(
            select(Post.repost_of_id, func.count())
            .where(Post.repost_of_id.in_(ids), Post.deleted_at.is_(None))
            .group_by(Post.repost_of_id)
        )
    ).all()
    likes = {pid: n for pid, n in like_rows}
    replies = {pid: n for pid, n in reply_rows if pid is not None}
    reposts = {pid: n for pid, n in repost_rows if pid is not None}
    return likes, replies, reposts


async def _viewer_flags(
    db: AsyncSession, viewer_id: uuid.UUID, ids: list[uuid.UUID]
) -> tuple[set[uuid.UUID], set[uuid.UUID]]:
    if not ids:
        return set(), set()
    liked = set(
        (await db.scalars(
            select(Like.post_id).where(Like.user_id == viewer_id, Like.post_id.in_(ids))
        )).all()
    )
    reposted_rows = (await db.scalars(
        select(Post.repost_of_id).where(
            Post.author_id == viewer_id,
            Post.repost_of_id.in_(ids),
            Post.text.is_(None),
            Post.deleted_at.is_(None),
        )
    )).all()
    reposted = {r for r in reposted_rows if r is not None}
    return liked, reposted


async def build_posts(db: AsyncSession, posts: list[Post], viewer: User) -> list[PostRead]:
    if not posts:
        return []

    # Pull in the one-level embeds (reposted/replied-to source posts).
    embed_ids = {
        ref
        for p in posts
        for ref in (p.repost_of_id, p.parent_id)
        if ref is not None and ref not in {x.id for x in posts}
    }
    embeds: list[Post] = []
    if embed_ids:
        embeds = list(
            (await db.scalars(select(Post).where(Post.id.in_(embed_ids)))).all()
        )

    by_id = {p.id: p for p in [*posts, *embeds]}
    all_ids = list(by_id.keys())
    likes, replies, reposts = await _counts(db, all_ids)
    liked_set, reposted_set = await _viewer_flags(db, viewer.id, all_ids)

    def to_read(p: Post, depth: int) -> PostRead:
        pr = PostRead.model_validate(p)
        pr.like_count = likes.get(p.id, 0)
        pr.reply_count = replies.get(p.id, 0)
        pr.repost_count = reposts.get(p.id, 0)
        pr.liked_by_me = p.id in liked_set
        pr.reposted_by_me = p.id in reposted_set
        if depth > 0:
            if p.repost_of_id and p.repost_of_id in by_id:
                pr.repost_of = to_read(by_id[p.repost_of_id], depth - 1)
            if p.parent_id and p.parent_id in by_id:
                pr.reply_to = to_read(by_id[p.parent_id], depth - 1)
        return pr

    return [to_read(p, 1) for p in posts]


async def get_post(db: AsyncSession, post_id: uuid.UUID, viewer: User) -> PostRead:
    post = await _alive(db, post_id)
    return (await build_posts(db, [post], viewer))[0]


def _page(rows: list[Post], limit: int) -> tuple[list[Post], str | None]:
    has_more = len(rows) > limit
    rows = rows[:limit]
    cursor = str(rows[-1].id) if has_more and rows else None
    return rows, cursor


async def home_timeline(
    db: AsyncSession, viewer: User, limit: int, before: uuid.UUID | None
) -> PostPage:
    limit = max(1, min(limit, MAX_PAGE))
    followees = select(Follow.followee_id).where(Follow.follower_id == viewer.id)
    q = (
        select(Post)
        .where(
            Post.deleted_at.is_(None),
            Post.parent_id.is_(None),
            or_(Post.author_id == viewer.id, Post.author_id.in_(followees)),
        )
        .order_by(Post.id.desc())
        .limit(limit + 1)
    )
    if before is not None:
        q = q.where(Post.id < before)
    rows, cursor = _page(list((await db.scalars(q)).all()), limit)
    return PostPage(posts=await build_posts(db, rows, viewer), next_cursor=cursor)


async def user_feed(
    db: AsyncSession,
    author_id: uuid.UUID,
    viewer: User,
    limit: int,
    before: uuid.UUID | None,
) -> PostPage:
    limit = max(1, min(limit, MAX_PAGE))
    q = (
        select(Post)
        .where(
            Post.author_id == author_id,
            Post.deleted_at.is_(None),
            Post.parent_id.is_(None),
        )
        .order_by(Post.id.desc())
        .limit(limit + 1)
    )
    if before is not None:
        q = q.where(Post.id < before)
    rows, cursor = _page(list((await db.scalars(q)).all()), limit)
    return PostPage(posts=await build_posts(db, rows, viewer), next_cursor=cursor)


async def list_replies(
    db: AsyncSession,
    post_id: uuid.UUID,
    viewer: User,
    limit: int,
    after: uuid.UUID | None,
) -> PostPage:
    limit = max(1, min(limit, MAX_PAGE))
    q = (
        select(Post)
        .where(Post.parent_id == post_id, Post.deleted_at.is_(None))
        .order_by(Post.id.asc())
        .limit(limit + 1)
    )
    if after is not None:
        q = q.where(Post.id > after)
    rows, cursor = _page(list((await db.scalars(q)).all()), limit)
    return PostPage(posts=await build_posts(db, rows, viewer), next_cursor=cursor)


async def posts_count(db: AsyncSession, author_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count())
            .select_from(Post)
            .where(
                Post.author_id == author_id,
                Post.deleted_at.is_(None),
                Post.parent_id.is_(None),
            )
        )
    ) or 0
