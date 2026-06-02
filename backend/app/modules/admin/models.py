import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamped
from app.core.ids import uuid7

# Report target kinds + lifecycle.
POST = "post"
USER = "user"
OPEN = "open"
RESOLVED = "resolved"
DISMISSED = "dismissed"


class Report(Timestamped, Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid7)
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    target_type: Mapped[str] = mapped_column(sa.String(8))  # "post" | "user"
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("posts.id", ondelete="CASCADE"), default=None
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), default=None
    )
    reason: Mapped[str] = mapped_column(sa.String(280), default="")
    status: Mapped[str] = mapped_column(
        sa.String(12), default=OPEN, server_default=OPEN, index=True
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), default=None
    )
