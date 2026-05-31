import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, Timestamped
from app.core.ids import uuid7
from app.modules.users.models import User

# Message content types
MSG_TEXT = "text"
MSG_IMAGE = "image"
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
