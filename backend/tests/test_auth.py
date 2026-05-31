from httpx import AsyncClient

REG = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "password123",
    "display_name": "Alice",
}


async def _register(client: AsyncClient, **overrides):
    return await client.post("/api/auth/register", json={**REG, **overrides})


async def _code(redis) -> str:
    code = await redis.get(f"emailcode:{REG['email']}")
    assert code is not None
    return code


async def test_register_sends_code(client: AsyncClient, fake_redis):
    resp = await _register(client)
    assert resp.status_code == 201
    code = await fake_redis.get(f"emailcode:{REG['email']}")
    assert code is not None and len(code) == 6


async def test_register_duplicate_conflicts(client: AsyncClient, fake_redis):
    await _register(client)
    resp = await _register(client)
    assert resp.status_code == 409


async def test_register_validates_input(client: AsyncClient, fake_redis):
    resp = await _register(client, password="short")
    assert resp.status_code == 422


async def test_verify_then_fetch_me(client: AsyncClient, fake_redis):
    await _register(client)
    resp = await client.post(
        "/api/auth/verify-email", json={"email": REG["email"], "code": await _code(fake_redis)}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == REG["email"]
    assert me.json()["email_verified"] is True


async def test_verify_wrong_code_rejected(client: AsyncClient, fake_redis):
    await _register(client)
    resp = await client.post(
        "/api/auth/verify-email", json={"email": REG["email"], "code": "000000"}
    )
    assert resp.status_code == 400


async def test_login_blocked_until_verified(client: AsyncClient, fake_redis):
    await _register(client)
    resp = await client.post(
        "/api/auth/login", json={"email": REG["email"], "password": REG["password"]}
    )
    assert resp.status_code == 403


async def test_login_refresh_logout_flow(client: AsyncClient, fake_redis):
    await _register(client)
    await client.post(
        "/api/auth/verify-email", json={"email": REG["email"], "code": await _code(fake_redis)}
    )

    login = await client.post(
        "/api/auth/login", json={"email": REG["email"], "password": REG["password"]}
    )
    assert login.status_code == 200
    assert login.json()["access_token"]
    assert client.cookies.get("refresh_token")

    refresh = await client.post("/api/auth/refresh")
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]

    logout = await client.post("/api/auth/logout")
    assert logout.status_code == 200
    # Old refresh was revoked → subsequent refresh fails.
    again = await client.post("/api/auth/refresh")
    assert again.status_code == 401


async def test_refresh_without_cookie_unauthorized(client: AsyncClient, fake_redis):
    resp = await client.post("/api/auth/refresh")
    assert resp.status_code == 401


async def test_wrong_password_rejected(client: AsyncClient, fake_redis):
    await _register(client)
    await client.post(
        "/api/auth/verify-email", json={"email": REG["email"], "code": await _code(fake_redis)}
    )
    resp = await client.post(
        "/api/auth/login", json={"email": REG["email"], "password": "wrongpassword"}
    )
    assert resp.status_code == 401


async def test_login_rate_limited(client: AsyncClient, fake_redis):
    payload = {"email": "ghost@example.com", "password": "whatever12"}
    statuses = [
        (await client.post("/api/auth/login", json=payload)).status_code for _ in range(11)
    ]
    assert statuses[-1] == 429
