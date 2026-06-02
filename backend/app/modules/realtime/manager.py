import asyncio
import json
import logging
import uuid

from fastapi import WebSocket

from app.core.redis import get_redis

_logger = logging.getLogger("app.realtime")


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


manager = ConnectionManager()


async def pubsub_listener() -> None:
    """Single global listener per process, receiving all user events and routing locally."""
    while True:
        pubsub = get_redis().pubsub()
        try:
            await pubsub.psubscribe("user:*")
            async for message in pubsub.listen():
                if message.get("type") != "pmessage":
                    continue
                
                channel_raw = message.get("channel", b"")
                channel = (
                    channel_raw.decode("utf-8")
                    if isinstance(channel_raw, bytes)
                    else channel_raw
                )
                if not channel.startswith("user:"):
                    continue
                    
                try:
                    user_id_str = channel.split(":")[1]
                    user_id = uuid.UUID(user_id_str)
                except (IndexError, ValueError):
                    continue
                
                local_conns = manager._local.get(user_id)
                if not local_conns:
                    continue

                try:
                    event = json.loads(message["data"])
                    for ws in list(local_conns):
                        try:
                            await ws.send_json(event)
                        except Exception:
                            pass
                except json.JSONDecodeError:
                    continue
        except asyncio.CancelledError:
            break
        except Exception:
            _logger.warning("Global pubsub error; reconnecting", exc_info=True)
            await asyncio.sleep(2)
        finally:
            try:
                await pubsub.aclose()
            except Exception:
                pass
