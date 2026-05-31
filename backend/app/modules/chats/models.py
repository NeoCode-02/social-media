import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, Timestamped, UUIDPrimaryKey
from app.modules.users.models import User

# Chat types
CHAT_DM = "dm"
CHAT_GROUP = "group"

# Member roles
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_MEMBER = "member"


class Chat(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "chats"

    type: Mapped[str] = mapped_column(sa.String(16))
    title: Mapped[str | None] = mapped_column(sa.String(128), default=None)
    avatar_url: Mapped[str | None] = mapped_column(sa.String(512), default=None)
    created_by: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    # Deterministic key for 1:1 DMs ("{min_id}:{max_id}"); NULL for groups.
    dm_key: Mapped[str | None] = mapped_column(sa.String(80), unique=True, default=None)

    members: Mapped[list["ChatMember"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan", lazy="selectin"
    )


class ChatMember(Timestamped, Base):
    __tablename__ = "chat_members"

    chat_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(sa.String(16), default=ROLE_MEMBER)
    # Last message this member has read (no FK: avoids chat<->message cycle).
    last_read_message_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid, default=None)

    chat: Mapped[Chat] = relationship(back_populates="members")
    user: Mapped[User] = relationship(lazy="selectin")
