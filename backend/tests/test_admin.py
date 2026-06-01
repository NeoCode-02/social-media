import pytest
from httpx import AsyncClient

from app.core.config import settings
from tests.test_posts import _make_user


@pytest.fixture
def admin_email(monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "admin@example.com")
    return "admin@example.com"


async def test_admin_access_and_user_moderation(client: AsyncClient, fake_redis, admin_email):
    a_h, a_id = await _make_user(client, fake_redis, admin_email, "boss")
    u_h, u_id = await _make_user(client, fake_redis, "au_u@example.com", "regular")

    # Admin email was auto-promoted; the regular user is not an admin.
    assert (await client.get("/api/users/me", headers=a_h)).json()["is_admin"] is True
    assert (await client.get("/api/admin/stats", headers=u_h)).status_code == 403

    stats = (await client.get("/api/admin/stats", headers=a_h)).json()
    assert stats["total_users"] >= 2 and stats["admins"] >= 1

    # Ban → the user's token is rejected everywhere; unban restores it.
    assert (await client.post(f"/api/admin/users/{u_id}/ban", headers=a_h)).status_code == 200
    assert (await client.get("/api/users/me", headers=u_h)).status_code == 403
    assert (await client.post(f"/api/admin/users/{u_id}/unban", headers=a_h)).status_code == 200
    assert (await client.get("/api/users/me", headers=u_h)).status_code == 200

    # Promote / demote.
    assert (await client.post(f"/api/admin/users/{u_id}/promote", headers=a_h)).json()["is_admin"]
    await client.post(f"/api/admin/users/{u_id}/demote", headers=a_h)
    assert (await client.get("/api/users/me", headers=u_h)).json()["is_admin"] is False

    # Self-guards.
    assert (await client.post(f"/api/admin/users/{a_id}/ban", headers=a_h)).status_code == 400
    assert (await client.delete(f"/api/admin/users/{a_id}", headers=a_h)).status_code == 400


async def test_admin_content_moderation_and_reports(client: AsyncClient, fake_redis, admin_email):
    a_h, _ = await _make_user(client, fake_redis, admin_email, "mod")
    u_h, _ = await _make_user(client, fake_redis, "ar_u@example.com", "poster")
    v_h, _ = await _make_user(client, fake_redis, "ar_v@example.com", "watcher")

    pid = (await client.post("/api/posts", json={"text": "bad post"}, headers=u_h)).json()["id"]

    # Admin sees and can delete any post.
    listing = (await client.get("/api/admin/posts?q=bad", headers=a_h)).json()
    assert any(p["id"] == pid for p in listing["posts"])
    assert (await client.delete(f"/api/admin/posts/{pid}", headers=a_h)).status_code == 200
    assert (await client.get(f"/api/posts/{pid}", headers=u_h)).status_code == 404

    # A user files a report → it lands in the open queue → resolve clears it.
    pid2 = (await client.post("/api/posts", json={"text": "spammy"}, headers=u_h)).json()["id"]
    payload = {"target_type": "post", "target_id": pid2, "reason": "spam"}
    r = await client.post("/api/reports", json=payload, headers=v_h)
    assert r.status_code == 204
    queue = (await client.get("/api/admin/reports?status=open", headers=a_h)).json()
    match = [x for x in queue["reports"] if x["post"] and x["post"]["id"] == pid2]
    assert len(match) == 1
    rid = match[0]["id"]
    assert (await client.post(f"/api/admin/reports/{rid}/resolve", headers=a_h)).status_code == 204
    still_open = (await client.get("/api/admin/reports?status=open", headers=a_h)).json()
    assert all(x["id"] != rid for x in still_open["reports"])
    resolved = (await client.get("/api/admin/reports?status=resolved", headers=a_h)).json()
    assert any(x["id"] == rid for x in resolved["reports"])
