import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamped

# Follow lifecycle. Public accounts jump straight to ACCEPTED; private accounts
# create a PENDING row that the followee must approve.
PENDING = "pending"
ACCEPTED = "accepted"


class Follow(Timestamped, Base):
    __tablename__ = "follows"

    follower_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    followee_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    status: Mapped[str] = mapped_column(
        sa.String(16), default=ACCEPTED, server_default=ACCEPTED, index=True
    )
