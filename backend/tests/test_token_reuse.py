from httpx import AsyncClient


async def _make_user_with_refresh(
    client: AsyncClient, fake_redis, email: str, username: str
) -> str:
    """Return only the initial refresh token (string) — needed for the
    rotation/reuse test which passes it via cookies, not as a header."""
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
    return resp.cookies.get("refresh_token")


async def test_refresh_token_reuse_detection(
    client: AsyncClient, fake_redis
):
    # 1. Register and get first refresh token
    rt1 = await _make_user_with_refresh(client, fake_redis, "victim@example.com", "victim")
    assert rt1 is not None

    # 2. Rotate once to get rt2
    resp2 = await client.post("/api/auth/refresh", cookies={"refresh_token": rt1})
    assert resp2.status_code == 200
    rt2 = resp2.cookies.get("refresh_token")
    assert rt2 is not None
    assert rt1 != rt2

    # 3. Attacker tries to reuse rt1
    resp_attack = await client.post("/api/auth/refresh", cookies={"refresh_token": rt1})
    assert resp_attack.status_code == 401
    assert "Security breach detected" in resp_attack.json()["detail"]

    # 4. Verify that rt2 is also invalidated now
    resp_victim = await client.post("/api/auth/refresh", cookies={"refresh_token": rt2})
    assert resp_victim.status_code == 401
