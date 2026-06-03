import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.db import SessionLocal
from app.core.redis import get_redis
from app.modules.auth.service import verify_ws_ticket
from app.modules.chats.models import ChatMember
from app.modules.messages.models import Message
from app.modules.realtime import events
from app.modules.realtime.manager import manager
from app.modules.users.models import User

router = APIRouter(tags=["realtime"])


# Redis key set when an admin bans/deletes a user so live sockets are kicked
# out within seconds, not only on next (re)connect. Cleared on logout. 24h
# TTL is plenty — a ban lives until an admin undoes it.
_REVOKED_KEY = "user_revoked:{user_id}"

# How often the connection checks the revoked flag. Cheap (one Redis GET).
_REVOKE_CHECK_INTERVAL_S = 5


async def _authenticate(ticket: str) -> uuid.UUID | None:
    user_id_str = await verify_ws_ticket(ticket)
    if not user_id_str:
        return None
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return None
    async with SessionLocal() as db:
        user = await db.get(User, user_id)
        if user is None or not user.email_verified:
            return None
    return user_id


async def _is_revoked(user_id: uuid.UUID) -> bool:
    return bool(await get_redis().exists(_REVOKED_KEY.format(user_id=user_id)))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, ticket: str = Query(...)) -> None:
    user_id = await _authenticate(ticket)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user_id, websocket)
    if manager.online_count(user_id) == 1:
        async with SessionLocal() as db:
            await events.publish_presence(db, user_id, "online")

    # Background revoker: wakes every few seconds, checks the Redis revocation
    # flag, and closes the socket if the user was banned mid-session.
    revoke_task: asyncio.Task[None] | None = None

    async def _watch_revocation() -> None:
        try:
            while True:
                await asyncio.sleep(_REVOKE_CHECK_INTERVAL_S)
                if await _is_revoked(user_id):
                    # 4403 is a custom app-level close code; FastAPI clients
                    # see it as a normal close with reason.
                    await websocket.close(code=4403)
                    return
        except (asyncio.CancelledError, Exception):
            return

    revoke_task = asyncio.create_task(_watch_revocation())

    try:
        while True:
            data = await websocket.receive_json()
            await _handle_client_event(user_id, data)
    except WebSocketDisconnect:
        pass
    finally:
        if revoke_task is not None:
            revoke_task.cancel()
            try:
                await revoke_task
            except (asyncio.CancelledError, Exception):
                pass
        manager.disconnect(user_id, websocket)
        if manager.online_count(user_id) == 0:
            async with SessionLocal() as db:
                user = await db.get(User, user_id)
                if user is not None:
                    user.last_seen = datetime.now(UTC)
                    await db.commit()
                await events.publish_presence(db, user_id, "offline")


async def _handle_client_event(user_id: uuid.UUID, data: dict[str, Any]) -> None:
    event_type = data.get("type")
    chat_id_raw = data.get("chat_id")
    if not chat_id_raw:
        return
    try:
        chat_id = uuid.UUID(chat_id_raw)
    except ValueError:
        return

    async with SessionLocal() as db:
        member = await db.get(ChatMember, {"chat_id": chat_id, "user_id": user_id})
        if member is None:  # not a member → ignore
            return

        if event_type in ("typing.start", "typing.stop"):
            await events.publish_typing(db, chat_id, user_id, event_type == "typing.start")
        elif event_type == "message.read" and data.get("last_read_message_id"):
            try:
                message_id = uuid.UUID(data["last_read_message_id"])
            except ValueError:
                return
            # Validate the message belongs to this chat (parity with the HTTP
            # mark_read path) so a client can't poison its own unread counter
            # with an arbitrary id.
            message = await db.get(Message, message_id)
            if message is None or message.chat_id != chat_id:
                return
            # Forward-only: ignore acks older than what we already recorded.
            current = member.last_read_message_id
            if current is not None and message_id <= current:
                return
            member.last_read_message_id = message_id
            await db.commit()
            await events.publish_read(db, chat_id, user_id, message_id)


async def mark_user_revoked(user_id: uuid.UUID, ttl_seconds: int = 60 * 60 * 24) -> None:
    """Stamp the revocation flag in Redis. The live socket watcher will close
    the connection within a few seconds. Call with `await` from async endpoints.
    """
    await get_redis().set(_REVOKED_KEY.format(user_id=user_id), "1", ex=ttl_seconds)

