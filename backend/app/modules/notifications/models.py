import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamped
from app.core.ids import uuid7

# Notification kinds.
LIKE = "like"
REPLY = "reply"
FOLLOW = "follow"
FOLLOW_REQUEST = "follow_request"
FOLLOW_ACCEPT = "follow_accept"
MENTION = "mention"


class Notification(Timestamped, Base):
    __tablename__ = "notifications"
    __table_args__ = (sa.Index("ix_notifications_recipient_id_id", "recipient_id", "id"),)

    # Time-ordered UUIDv7 → doubles as the chronological cursor.
    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid7)
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(sa.String(32))
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("posts.id", ondelete="CASCADE"), default=None
    )
    read_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), default=None
    )
