import json
import uuid

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.modules.realtime.events import _publish
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
    # We mock _user_pubsub_listener because we want to test direct deliver (if used)
    # or just the registry. deliver() is deprecated but we can still test the logic.
    await manager.connect(u1, ws1)  # type: ignore[arg-type]
    await manager.connect(u2, ws2)  # type: ignore[arg-type]

    assert ws1.accepted and ws2.accepted

    # Since we are not running a real Redis, we'll manually call send_json
    # to simulate what the listener would do.
    for ws in manager._local.get(u1, []):
        await ws.send_json({"type": "hello"})

    assert ws1.sent == [{"type": "hello"}]
    assert ws2.sent == []

    manager.disconnect(u1, ws1)  # type: ignore[arg-type]
    assert manager.online_count(u1) == 0


async def test_publish_writes_envelope_to_channel(fake_redis):
    pub1 = fake_redis.pubsub()
    u1 = uuid.uuid4()
    await pub1.subscribe(f"user:{u1}")

    # Consume the subscribe message
    await pub1.get_message(timeout=1)

    await _publish([u1], {"type": "ping"})

    msg1 = await pub1.get_message(timeout=1)
    assert msg1 is not None
    assert msg1["type"] == "message"
    assert json.loads(msg1["data"]) == {"type": "ping"}
    await pub1.aclose()


def test_ws_rejects_invalid_token():
    with TestClient(app) as client, pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?token=not-a-jwt") as ws:
            ws.receive_text()
