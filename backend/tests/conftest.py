from collections.abc import AsyncGenerator, Awaitable, Callable

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.core.redis as redis_module
import app.db_models  # noqa: F401  (populate Base.metadata)
from app.core.db import Base, get_db
from app.main import app


@pytest.fixture
async def db_sessionmaker() -> AsyncGenerator[async_sessionmaker, None]:
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def fake_redis(monkeypatch) -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    # get_redis() returns this module-level singleton.
    monkeypatch.setattr(redis_module, "_redis", fake)
    yield fake
    await fake.aclose()


@pytest.fixture
async def client(
    db_sessionmaker: async_sessionmaker,
    fake_redis: fakeredis.aioredis.FakeRedis,
    monkeypatch,
) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        async with db_sessionmaker() as session:
            yield session

    async def _noop_enqueue(*args, **kwargs) -> None:
        return None

    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr("app.modules.auth.service.enqueue", _noop_enqueue)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Shared test helper: register a user, verify email, return (auth_headers, user_id).
# Tests that previously had their own _make_user can request this fixture and
# call it with whatever email/username they need.
MakeUser = Callable[[str, str], Awaitable[tuple[dict[str, str], str]]]


@pytest.fixture
def make_user(
    client: AsyncClient, fake_redis: fakeredis.aioredis.FakeRedis
) -> MakeUser:
    async def _impl(email: str, username: str) -> tuple[dict[str, str], str]:
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

    return _impl
