from httpx import AsyncClient

REG = {
    "email": "bob@example.com",
    "username": "bob",
    "password": "password123",
    "display_name": "Bob",
}


async def _verified_headers(client: AsyncClient, fake_redis) -> dict[str, str]:
    await client.post("/api/auth/register", json=REG)
    code = await fake_redis.get(f"emailcode:{REG['email']}")
    resp = await client.post("/api/auth/verify-email", json={"email": REG["email"], "code": code})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_me_requires_auth(client: AsyncClient, fake_redis):
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


async def test_update_display_name(client: AsyncClient, fake_redis):
    headers = await _verified_headers(client, fake_redis)
    resp = await client.patch("/api/users/me", json={"display_name": "Bobby"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Bobby"


async def test_avatar_upload_url(client: AsyncClient, fake_redis):
    headers = await _verified_headers(client, fake_redis)
    resp = await client.post(
        "/api/users/me/avatar-url", json={"content_type": "image/png"}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["key"].startswith("avatars/")
    assert body["upload_url"].startswith("http")
    assert body["public_url"].endswith(body["key"])


async def test_avatar_rejects_bad_type(client: AsyncClient, fake_redis):
    headers = await _verified_headers(client, fake_redis)
    resp = await client.post(
        "/api/users/me/avatar-url", json={"content_type": "application/pdf"}, headers=headers
    )
    assert resp.status_code == 422
