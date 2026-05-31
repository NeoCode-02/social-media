import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, Timestamped, UUIDPrimaryKey


class User(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(sa.String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(sa.String(64))
    # Nullable for OAuth-only accounts that never set a password.
    password_hash: Mapped[str | None] = mapped_column(sa.String(255), default=None)
    email_verified: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    avatar_url: Mapped[str | None] = mapped_column(sa.String(512), default=None)
    bio: Mapped[str | None] = mapped_column(sa.String(280), default=None)
    location: Mapped[str | None] = mapped_column(sa.String(64), default=None)
    website: Mapped[str | None] = mapped_column(sa.String(255), default=None)
    last_seen: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), default=None)

    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class OAuthAccount(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(sa.String(32))  # e.g. "google"
    provider_user_id: Mapped[str] = mapped_column(sa.String(255))

    user: Mapped[User] = relationship(back_populates="oauth_accounts")
