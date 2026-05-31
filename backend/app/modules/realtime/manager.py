import asyncio
import json
import uuid
from collections.abc import Iterable
from typing import Any

from fastapi import WebSocket

from app.core.redis import get_redis
from app.modules.realtime.events import CHANNEL


class ConnectionManager:
    """Process-local registry of user_id -> open websockets."""

    def __init__(self) -> None:
        self._local: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._local.setdefault(user_id, set()).add(ws)

    def disconnect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        conns = self._local.get(user_id)
        if conns is not None:
            conns.discard(ws)
            if not conns:
                del self._local[user_id]

    def online_count(self, user_id: uuid.UUID) -> int:
        return len(self._local.get(user_id, ()))

    async def deliver(self, recipients: Iterable[str], event: dict[str, Any]) -> None:
        for raw in recipients:
            try:
                key = uuid.UUID(raw)
            except ValueError:
                continue
            for ws in list(self._local.get(key, ())):
                try:
                    await ws.send_json(event)
                except Exception:
                    # Drop broken sockets; the receive loop will clean up.
                    pass


manager = ConnectionManager()


async def pubsub_listener() -> None:
    """Subscribe to the Redis channel and fan events out to local sockets.

    Started once per process from the app lifespan.
    """
    pubsub = get_redis().pubsub()
    await pubsub.subscribe(CHANNEL)
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                data = json.loads(message["data"])
                await manager.deliver(data["recipients"], data["event"])
            except (json.JSONDecodeError, KeyError):
                continue
    except asyncio.CancelledError:
        raise
    finally:
        await pubsub.aclose()
