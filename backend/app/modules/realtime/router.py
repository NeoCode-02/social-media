import uuid
from datetime import UTC, datetime
from typing import Any

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.db import SessionLocal
from app.core.security import decode_token
from app.modules.chats.models import ChatMember
from app.modules.realtime import events
from app.modules.realtime.manager import manager
from app.modules.users.models import User

router = APIRouter(tags=["realtime"])


async def _authenticate(token: str) -> uuid.UUID | None:
    try:
        payload = decode_token(token, "access")
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        return None
    async with SessionLocal() as db:
        user = await db.get(User, user_id)
        if user is None or not user.email_verified:
            return None
    return user_id


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)) -> None:
    user_id = await _authenticate(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user_id, websocket)
    if manager.online_count(user_id) == 1:
        async with SessionLocal() as db:
            await events.publish_presence(db, user_id, "online")

    try:
        while True:
            data = await websocket.receive_json()
            await _handle_client_event(user_id, data)
    except WebSocketDisconnect:
        pass
    finally:
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
            member.last_read_message_id = message_id
            await db.commit()
            await events.publish_read(db, chat_id, user_id, message_id)
