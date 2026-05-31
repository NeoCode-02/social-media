from httpx import AsyncClient


async def test_request_id_header_present(client: AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID")


async def test_request_id_is_echoed(client: AsyncClient) -> None:
    resp = await client.get("/api/health", headers={"X-Request-ID": "test-123"})
    assert resp.headers.get("X-Request-ID") == "test-123"


async def test_security_headers(client: AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
