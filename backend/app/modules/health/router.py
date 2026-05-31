from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.redis import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — process is up."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Readiness probe — dependencies (Postgres, Redis) reachable."""
    await db.execute(text("SELECT 1"))
    await get_redis().ping()
    return {"status": "ready", "db": "ok", "redis": "ok"}
