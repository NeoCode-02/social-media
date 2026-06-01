import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, Timestamped
from app.core.ids import uuid7
from app.modules.messages.models import Attachment
from app.modules.users.models import User

# Post kinds are derived, not stored: a row with repost_of_id and no text is a
# pure repost; with text it's a quote; with parent_id it's a reply.


class Post(Timestamped, Base):
    __tablename__ = "posts"
    __table_args__ = (sa.Index("ix_posts_author_id_id", "author_id", "id"),)

    # Time-ordered UUIDv7 → primary key doubles as the chronological cursor.
    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid7)
    author_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str | None] = mapped_column(sa.Text, default=None)
    # Reply target (this post is a reply to parent_id).
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("posts.id", ondelete="SET NULL"), default=None, index=True
    )
    # Repost/quote source (this post reposts repost_of_id).
    repost_of_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("posts.id", ondelete="SET NULL"), default=None, index=True
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), default=None
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), default=None
    )

    author: Mapped[User] = relationship(lazy="selectin")
    attachments: Mapped[list[Attachment]] = relationship(
        lazy="selectin",
        primaryjoin="Post.id == Attachment.post_id",
        foreign_keys="Attachment.post_id",
        cascade="all, delete-orphan",
    )


class Like(Timestamped, Base):
    __tablename__ = "likes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class PostView(Timestamped, Base):
    """One row per (viewer, post) — counted as a unique impression."""

    __tablename__ = "post_views"

    post_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    viewer_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class PostHashtag(Timestamped, Base):
    """A #tag occurrence on a post. created_at powers trending windows."""

    __tablename__ = "post_hashtags"

    post_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(sa.String(50), primary_key=True, index=True)
