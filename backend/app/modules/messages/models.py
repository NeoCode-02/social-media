import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, Timestamped, UUIDPrimaryKey
from app.core.ids import uuid7
from app.core.storage import public_url
from app.modules.users.models import User

# Message content types
MSG_TEXT = "text"
MSG_IMAGE = "image"
MSG_VIDEO = "video"
MSG_AUDIO = "audio"
MSG_VOICE = "voice"
MSG_FILE = "file"


class Message(Timestamped, Base):
    __tablename__ = "messages"
    __table_args__ = (sa.Index("ix_messages_chat_id_id", "chat_id", "id"),)

    # Time-ordered UUIDv7 → primary key doubles as the chronological sort key.
    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid7)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("chats.id", ondelete="CASCADE"), index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    type: Mapped[str] = mapped_column(sa.String(16), default=MSG_TEXT)
    content: Mapped[str | None] = mapped_column(sa.Text, default=None)
    reply_to_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("messages.id", ondelete="SET NULL"), default=None
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), default=None
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), default=None
    )

    sender: Mapped[User] = relationship(lazy="selectin")
    attachments: Mapped[list["Attachment"]] = relationship(
        lazy="selectin",
        foreign_keys="Attachment.message_id",
        cascade="all, delete-orphan",
    )


class Attachment(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "attachments"
    __table_args__ = (
        # Speeds up `WHERE chat_id = ? ORDER BY created_at` — used by the
        # chat-scoped attachment scan during orphan cleanup and any future
        # "media gallery per chat" feature. Single-column chat_id index alone
        # forces a sort on the result.
        sa.Index("ix_attachments_chat_id_created_at", "chat_id", "created_at"),
    )

    # NULL until the message that owns it is sent (upload happens first).
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("messages.id", ondelete="CASCADE"), index=True, default=None
    )
    # An attachment belongs to either a chat message or a feed post.
    chat_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("chats.id", ondelete="CASCADE"), index=True, default=None
    )
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("posts.id", ondelete="CASCADE"), index=True, default=None
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    storage_key: Mapped[str] = mapped_column(sa.String(512))
    thumbnail_key: Mapped[str | None] = mapped_column(sa.String(512), default=None)
    mime: Mapped[str] = mapped_column(sa.String(128))
    name: Mapped[str] = mapped_column(sa.String(255))
    size: Mapped[int] = mapped_column(sa.BigInteger)
    width: Mapped[int | None] = mapped_column(sa.Integer, default=None)
    height: Mapped[int | None] = mapped_column(sa.Integer, default=None)
    # Audio/video length in milliseconds (client-reported).
    duration_ms: Mapped[int | None] = mapped_column(sa.Integer, default=None)
    # Force render as a downloadable file card even for images.
    as_file: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    # Recorded voice note (compact inline player) vs an uploaded audio file.
    is_voice: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    @property
    def url(self) -> str:
        return public_url(self.storage_key)

    @property
    def thumbnail_url(self) -> str:
        return public_url(self.thumbnail_key or self.storage_key)
