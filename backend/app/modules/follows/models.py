import enum
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamped


class FollowStatus(enum.StrEnum):
    """Follow lifecycle. Public accounts jump straight to ACCEPTED; private
    accounts create a PENDING row that the followee must approve.

    NOTE: stored as a plain VARCHAR in Postgres (see the column below) for
    schema-portability and to avoid a Postgres-only `CREATE TYPE` round
    trip in dev. The enum gives us type-safe comparisons in Python; the
    DB just sees a string.
    """

    PENDING = "pending"
    ACCEPTED = "accepted"


# Backwards-compatible module-level constants so existing
# `from app.modules.follows.models import PENDING` imports keep working.
PENDING = FollowStatus.PENDING.value
ACCEPTED = FollowStatus.ACCEPTED.value


class Follow(Timestamped, Base):
    __tablename__ = "follows"

    follower_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    followee_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    status: Mapped[FollowStatus] = mapped_column(
        # String column, not Postgres ENUM — the Python enum above gives
        # us validation/comparison safety in code without forcing a
        # database migration to add a new custom type.
        sa.String(16),
        default=FollowStatus.ACCEPTED,
        server_default=FollowStatus.ACCEPTED.value,
        index=True,
    )
