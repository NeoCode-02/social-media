from httpx import AsyncClient

import app.modules.chats.router as chats_router
import app.modules.messages.service as msg_service


async def _make_user(
    client: AsyncClient, fake_redis, email: str, username: str
) -> tuple[dict[str, str], str]:
    await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "password123",
            "display_name": username,
        },
    )
    code = await fake_redis.get(f"emailcode:{email}")
    resp = await client.post("/api/auth/verify-email", json={"email": email, "code": code})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    me = await client.get("/api/users/me", headers=headers)
    return headers, me.json()["id"]


def _stub_storage(monkeypatch) -> None:
    # No MinIO in tests — neutralise the network calls.
    monkeypatch.setattr(msg_service, "put_object", lambda *a, **k: None)
    monkeypatch.setattr(
        chats_router, "presigned_get_url", lambda key, name=None: f"http://signed/{key}"
    )


async def test_profile_fields_roundtrip(client: AsyncClient, fake_redis):
    headers, uid = await _make_user(client, fake_redis, "p@example.com", "puser")

    patch = await client.patch(
        "/api/users/me",
        json={"bio": "hello world", "location": "Tashkent", "website": "example.com"},
        headers=headers,
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["bio"] == "hello world"
    assert body["location"] == "Tashkent"
    assert body["website"] == "example.com"

    # Public profile endpoint exposes the same fields.
    other_h, _ = await _make_user(client, fake_redis, "q@example.com", "quser")
    prof = await client.get(f"/api/users/{uid}", headers=other_h)
    assert prof.status_code == 200
    assert prof.json()["bio"] == "hello world"
    assert "email" not in prof.json()  # UserProfile is public, no email


async def test_profile_unknown_user_404(client: AsyncClient, fake_redis):
    headers, _ = await _make_user(client, fake_redis, "p@example.com", "puser")
    resp = await client.get(
        "/api/users/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert resp.status_code == 404


async def test_upload_as_file_and_download(client: AsyncClient, fake_redis, monkeypatch):
    _stub_storage(monkeypatch)
    a_h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")
    _, b_id = await _make_user(client, fake_redis, "b@example.com", "buser")
    cid = (
        await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    ).json()["id"]

    up = await client.post(
        f"/api/chats/{cid}/attachments",
        files={"file": ("report.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"as_file": "true"},
        headers=a_h,
    )
    assert up.status_code == 201
    att = up.json()
    assert att["as_file"] is True
    assert att["name"] == "report.pdf"
    aid = att["id"]

    # Sending it yields a "file" message type.
    msg = await client.post(
        f"/api/chats/{cid}/messages",
        json={"attachment_ids": [aid]},
        headers=a_h,
    )
    assert msg.status_code == 201
    assert msg.json()["type"] == "file"

    # Download URL is a signed link gated by membership.
    dl = await client.get(
        f"/api/chats/{cid}/attachments/{aid}/download-url", headers=a_h
    )
    assert dl.status_code == 200
    assert dl.json()["url"].startswith("http")


async def test_upload_voice_message(client: AsyncClient, fake_redis, monkeypatch):
    _stub_storage(monkeypatch)
    a_h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")
    _, b_id = await _make_user(client, fake_redis, "b@example.com", "buser")
    cid = (
        await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    ).json()["id"]

    up = await client.post(
        f"/api/chats/{cid}/attachments",
        files={"file": ("voice.webm", b"OggS fake", "audio/webm")},
        data={"is_voice": "true", "duration_ms": "4200"},
        headers=a_h,
    )
    assert up.status_code == 201
    att = up.json()
    assert att["is_voice"] is True
    assert att["duration_ms"] == 4200

    msg = await client.post(
        f"/api/chats/{cid}/messages", json={"attachment_ids": [att["id"]]}, headers=a_h
    )
    assert msg.json()["type"] == "voice"


async def test_download_url_blocks_non_member(client: AsyncClient, fake_redis, monkeypatch):
    _stub_storage(monkeypatch)
    a_h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")
    _, b_id = await _make_user(client, fake_redis, "b@example.com", "buser")
    c_h, _ = await _make_user(client, fake_redis, "c@example.com", "cuser")
    cid = (
        await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    ).json()["id"]
    up = await client.post(
        f"/api/chats/{cid}/attachments",
        files={"file": ("f.bin", b"data", "application/octet-stream")},
        data={"as_file": "true"},
        headers=a_h,
    )
    aid = up.json()["id"]

    blocked = await client.get(
        f"/api/chats/{cid}/attachments/{aid}/download-url", headers=c_h
    )
    assert blocked.status_code == 404
