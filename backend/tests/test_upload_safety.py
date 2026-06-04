"""Uploads can't smuggle a script-capable Content-Type past the public bucket.

The media bucket is world-readable, so anything that isn't a known inline-safe
type must be stored (and served) as an opaque octet-stream download.
"""
import io

from httpx import AsyncClient
from PIL import Image

import app.modules.chats.router as chats_router
import app.modules.messages.service as msg_service


def _stub_storage(monkeypatch) -> None:
    monkeypatch.setattr(msg_service, "put_object", lambda *a, **k: None)
    monkeypatch.setattr(
        chats_router, "presigned_get_url", lambda key, name=None: f"http://signed/{key}"
    )


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (3, 3), "red").save(buf, format="PNG")
    return buf.getvalue()


async def _dm(client: AsyncClient, a_h, b_id) -> str:
    return (
        await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    ).json()["id"]


async def test_svg_upload_coerced_to_octet_stream(client: AsyncClient, make_user, monkeypatch):
    _stub_storage(monkeypatch)
    a_h, _ = await make_user("us_a@example.com", "usa")
    _, b_id = await make_user("us_b@example.com", "usb")
    cid = await _dm(client, a_h, b_id)

    up = await client.post(
        f"/api/chats/{cid}/attachments",
        files={
            "file": (
                "evil.svg",
                b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>",
                "image/svg+xml",
            )
        },
        headers=a_h,
    )
    assert up.status_code == 201
    assert up.json()["mime"] == "application/octet-stream"


async def test_html_upload_coerced_to_octet_stream(client: AsyncClient, make_user, monkeypatch):
    _stub_storage(monkeypatch)
    a_h, _ = await make_user("us2_a@example.com", "us2a")
    _, b_id = await make_user("us2_b@example.com", "us2b")
    cid = await _dm(client, a_h, b_id)

    up = await client.post(
        f"/api/chats/{cid}/attachments",
        files={"file": ("page.html", b"<h1>hi</h1><script>alert(1)</script>", "text/html")},
        data={"as_file": "true"},
        headers=a_h,
    )
    assert up.status_code == 201
    assert up.json()["mime"] == "application/octet-stream"


async def test_real_image_still_normalized_to_webp(client: AsyncClient, make_user, monkeypatch):
    _stub_storage(monkeypatch)
    a_h, _ = await make_user("us3_a@example.com", "us3a")
    _, b_id = await make_user("us3_b@example.com", "us3b")
    cid = await _dm(client, a_h, b_id)

    up = await client.post(
        f"/api/chats/{cid}/attachments",
        files={"file": ("pic.png", _png_bytes(), "image/png")},
        headers=a_h,
    )
    assert up.status_code == 201
    assert up.json()["mime"] == "image/webp"  # legit images stay inline-renderable
