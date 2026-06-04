"""The email-verification code is burned after too many wrong guesses, so the
6-digit space can't be brute-forced from a pool of IPs."""
from httpx import AsyncClient

REG = {
    "email": "lock@example.com",
    "username": "locky",
    "password": "password123",
    "display_name": "Locky",
}


async def test_code_burned_after_max_attempts(client: AsyncClient, fake_redis):
    await client.post("/api/auth/register", json=REG)
    real = await fake_redis.get(f"emailcode:{REG['email']}")
    assert real is not None
    wrong = "654321" if real != "654321" else "123456"

    # Five wrong guesses (under the 20/min verify rate limit) burn the code.
    for _ in range(5):
        r = await client.post(
            "/api/auth/verify-email", json={"email": REG["email"], "code": wrong}
        )
        assert r.status_code == 400

    # The code is gone — even the correct value no longer verifies.
    assert await fake_redis.get(f"emailcode:{REG['email']}") is None
    r = await client.post(
        "/api/auth/verify-email", json={"email": REG["email"], "code": real}
    )
    assert r.status_code == 400


async def test_resending_a_code_resets_the_attempt_counter(client: AsyncClient, fake_redis):
    await client.post("/api/auth/register", json=REG)
    real = await fake_redis.get(f"emailcode:{REG['email']}")
    wrong = "654321" if real != "654321" else "123456"
    for _ in range(3):
        await client.post("/api/auth/verify-email", json={"email": REG["email"], "code": wrong})
    assert await fake_redis.get(f"emailcode_attempts:{REG['email']}") is not None

    # Simulate the 60s resend cooldown elapsing, then request a fresh code.
    await fake_redis.delete(f"emailcode_sent:{REG['email']}")
    resp = await client.post("/api/auth/resend-code", json={"email": REG["email"]})
    assert resp.status_code == 200

    # A fresh code clears the counter; the new code then verifies normally.
    new_code = await fake_redis.get(f"emailcode:{REG['email']}")
    assert await fake_redis.get(f"emailcode_attempts:{REG['email']}") is None
    r = await client.post(
        "/api/auth/verify-email", json={"email": REG["email"], "code": new_code}
    )
    assert r.status_code == 200
