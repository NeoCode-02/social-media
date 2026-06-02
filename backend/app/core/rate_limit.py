from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.redis import get_redis


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Only honor X-Forwarded-For behind a trusted proxy,
    otherwise a client can spoof the header to dodge the limiter."""
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(limit: int, window_seconds: int, scope: str):
    """Dependency factory: fixed-window limiter keyed by client IP + scope.

    Usage::

        @router.post("/login", dependencies=[Depends(rate_limit(10, 60, "login"))])
    """

    async def _dep(request: Request) -> None:
        key = f"rl:{scope}:{_client_ip(request)}"
        redis = get_redis()
        # Atomic incr + (first-time) expire so the window is always armed, even
        # if the process dies right after the increment.
        async with redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds, nx=True)
            count, _ = await pipe.execute()
        if count > limit:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded, retry in {max(ttl, 1)}s",
                headers={"Retry-After": str(max(ttl, 1))},
            )

    return Depends(_dep)
