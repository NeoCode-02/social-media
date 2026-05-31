import asyncio
import json
import logging
import uuid
from collections.abc import Iterable
from typing import Any

from fastapi import WebSocket

from app.core.redis import get_redis

_logger = logging.getLogger("app.realtime")


class ConnectionManager:
    """Process-local registry of user_id -> open websockets."""

    def __init__(self) -> None:
        self._local: dict[uuid.UUID, set[WebSocket]] = {}
        self._pubsub_tasks: dict[uuid.UUID, asyncio.Task] = {}

    async def connect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._local.setdefault(user_id, set()).add(ws)

        # If this is the first connection for this user on this instance,
        # start a dedicated pubsub listener for their channel.
        if len(self._local[user_id]) == 1:
            task = asyncio.create_task(self._user_pubsub_listener(user_id))
            self._pubsub_tasks[user_id] = task

    def disconnect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        conns = self._local.get(user_id)
        if conns is not None:
            conns.discard(ws)
            if not conns:
                del self._local[user_id]
                # Last connection closed for this user; stop their listener.
                task = self._pubsub_tasks.pop(user_id, None)
                if task:
                    task.cancel()

    def online_count(self, user_id: uuid.UUID) -> int:
        return len(self._local.get(user_id, ()))

    async def _user_pubsub_listener(self, user_id: uuid.UUID) -> None:
        """Subscribe to a specific user's Redis channel."""
        channel = f"user:{user_id}"
        while True:
            pubsub = get_redis().pubsub()
            try:
                await pubsub.subscribe(channel)
                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    try:
                        event = json.loads(message["data"])
                        # Deliver to all local sockets for this user.
                        for ws in list(self._local.get(user_id, ())):
                            try:
                                await ws.send_json(event)
                            except Exception:
                                pass
                    except json.JSONDecodeError:
                        continue
            except asyncio.CancelledError:
                break
            except Exception:
                _logger.warning(f"pubsub error for {channel}; reconnecting", exc_info=True)
                await asyncio.sleep(2)
            finally:
                try:
                    await pubsub.aclose()
                except Exception:
                    pass

    async def deliver(self, recipients: Iterable[str], event: dict[str, Any]) -> None:
        # DEPRECATED: This was for the global channel fan-out.
        # Now events are published directly to user channels in events.py.
        pass


manager = ConnectionManager()


async def pubsub_listener() -> None:
    """NO-OP: Now handled by per-user listeners in ConnectionManager."""
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
