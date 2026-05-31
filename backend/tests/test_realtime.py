import json
import uuid

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.modules.realtime.events import CHANNEL, _publish
from app.modules.realtime.manager import ConnectionManager


class FakeWS:
    def __init__(self) -> None:
        self.sent: list[dict] = []
        self.accepted = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)


async def test_manager_delivers_only_to_recipients():
    manager = ConnectionManager()
    u1, u2 = uuid.uuid4(), uuid.uuid4()
    ws1, ws2 = FakeWS(), FakeWS()
    await manager.connect(u1, ws1)  # type: ignore[arg-type]
    await manager.connect(u2, ws2)  # type: ignore[arg-type]

    assert ws1.accepted and ws2.accepted

    await manager.deliver([str(u1)], {"type": "hello"})
    assert ws1.sent == [{"type": "hello"}]
    assert ws2.sent == []

    manager.disconnect(u1, ws1)  # type: ignore[arg-type]
    assert manager.online_count(u1) == 0


async def test_publish_writes_envelope_to_channel(fake_redis):
    pubsub = fake_redis.pubsub()
    await pubsub.subscribe(CHANNEL)
    uid = uuid.uuid4()

    await _publish([uid], {"type": "ping"})

    received = None
    for _ in range(20):
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
        if msg is not None:
            received = msg
            break
    await pubsub.aclose()

    assert received is not None
    data = json.loads(received["data"])
    assert data["recipients"] == [str(uid)]
    assert data["event"] == {"type": "ping"}


def test_ws_rejects_invalid_token():
    with TestClient(app) as client, pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?token=not-a-jwt") as ws:
            ws.receive_text()
