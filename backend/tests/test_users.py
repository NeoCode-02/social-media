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


async def test_user_search(client: AsyncClient, fake_redis):
    headers = await _verified_headers(client, fake_redis)  # bob
    await client.post(
        "/api/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "password123",
            "display_name": "Alice",
        },
    )
    found = await client.get("/api/users/search?q=ali", headers=headers)
    assert found.status_code == 200
    assert "alice" in [u["username"] for u in found.json()]

    # self is excluded
    self_search = await client.get("/api/users/search?q=bob", headers=headers)
    assert all(u["username"] != "bob" for u in self_search.json())
