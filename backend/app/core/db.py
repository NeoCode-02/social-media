import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class UUIDPrimaryKey:
    """Mixin: UUID primary key (portable across Postgres and SQLite)."""

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)


class Timestamped:
    """Mixin: created_at / updated_at maintained server-side."""

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    # When a connection returns to the pool we want a clean ROLLBACK
    # issued *while we still own* the connection — not later when the
    # next user picks it up. The default is 'rollback' but make it
    # explicit so a future SQLAlchemy upgrade doesn't surprise us.
    pool_reset_on_return="rollback",
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a scoped async session.

    The session is closed inside a `try/except` that swallows the
    `InterfaceError` raised by asyncpg when the underlying connection
    has already been returned to the pool. The request itself has
    already completed by then — failing to log a clean ROLLBACK after
    the response is sent would just crash the worker.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            # `await` here ensures the connection is released cleanly
            # even if the endpoint raised — the implicit transaction
            # from SELECT statements must be closed before the
            # connection goes back to the pool.
            try:
                await session.close()
            except Exception:
                # `InterfaceError: cannot perform operation: another
                # operation is in progress` from asyncpg means the
                # connection is already gone. Safe to ignore.
                pass
