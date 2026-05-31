from fastapi import Depends, HTTPException, Request, status

from app.core.redis import get_redis


def rate_limit(limit: int, window_seconds: int, scope: str):
    """Dependency factory: fixed-window limiter keyed by client IP + scope.

    Usage::

        @router.post("/login", dependencies=[Depends(rate_limit(10, 60, "login"))])
    """

    async def _dep(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        key = f"rl:{scope}:{client}"
        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded, retry in {max(ttl, 1)}s",
                headers={"Retry-After": str(max(ttl, 1))},
            )

    return Depends(_dep)
