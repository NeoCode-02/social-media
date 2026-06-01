import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamped


class Block(Timestamped, Base):
    """blocker_id has blocked blocked_id (one-directional row; effect is mutual)."""

    __tablename__ = "blocks"

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    blocked_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class Mute(Timestamped, Base):
    """muter_id mutes muted_id — their posts are hidden from muter's feeds only."""

    __tablename__ = "mutes"

    muter_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    muted_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
