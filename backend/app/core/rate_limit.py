import time

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


def rate_limit(limit: int, window_seconds: int, scope: str, *, sliding: bool = False):
    """Dependency factory: rate limiter keyed by client IP + scope.

    ``sliding=False`` (default) uses a fixed window (cheap, but a client can
    burst 2*limit requests across a window boundary). ``sliding=True`` uses a
    sorted-set log of timestamps so the window is truly continuous — prefer
    this for security-sensitive routes (login, register, resend, refresh).

    Usage::

        @router.post("/login", dependencies=[Depends(rate_limit(10, 60, "login", sliding=True))])
    """

    async def _dep(request: Request) -> None:
        ip = _client_ip(request)
        key = f"rl:{scope}:{ip}"
        redis = get_redis()

        if sliding:
            # Sliding-window log: ZADD a unique member per request, prune
            # entries older than the window, then ZCARD to count.
            now_ms = int(time.time() * 1000)
            window_start = now_ms - window_seconds * 1000
            member = f"{now_ms}:{id(request)}"
            async with redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zadd(key, {member: now_ms})
                pipe.zcard(key)
                # Bound the set size so a flood can't grow it forever.
                pipe.expire(key, window_seconds + 1)
                _, _, count, _ = await pipe.execute()
            if count > limit:
                oldest = await redis.zrange(key, 0, 0, withscores=True)
                # When the oldest entry ages out, one slot frees up.
                if oldest:
                    retry = max(1, window_seconds - int((now_ms - oldest[0][1]) / 1000))
                else:
                    retry = 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded, retry in {retry}s",
                    headers={"Retry-After": str(retry)},
                )
        else:
            # Fixed-window: cheap, atomic. See note above about boundary bursts.
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
