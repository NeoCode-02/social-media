from httpx import AsyncClient


async def test_notifications_like_reply_follow_mention(client: AsyncClient, make_user):
    a_h, a_id = await make_user("no_a@example.com", "noah")
    b_h, b_id = await make_user("no_b@example.com", "bella")

    # B follows A (public → instant) → A gets a follow notification.
    await client.post(f"/api/users/{a_id}/follow", headers=b_h)

    pid = (await client.post("/api/posts", json={"text": "look"}, headers=a_h)).json()["id"]
    await client.post(f"/api/posts/{pid}/like", headers=b_h)
    await client.post("/api/posts", json={"text": "nice", "parent_id": pid}, headers=b_h)
    # A mentions @bella.
    await client.post("/api/posts", json={"text": "hey @bella"}, headers=a_h)
    # Self-like must not notify A.
    await client.post(f"/api/posts/{pid}/like", headers=a_h)

    page = (await client.get("/api/notifications", headers=a_h)).json()
    types = {n["type"] for n in page["notifications"]}
    assert {"follow", "like", "reply"} <= types
    assert all(n["actor"]["id"] == b_id for n in page["notifications"])  # never self
    assert page["unread_count"] == len(page["notifications"])

    bpage = (await client.get("/api/notifications", headers=b_h)).json()
    assert "mention" in {n["type"] for n in bpage["notifications"]}

    # Bulk mark read.
    assert (await client.post("/api/notifications/read", json={}, headers=a_h)).status_code == 204
    cnt = (await client.get("/api/notifications/unread-count", headers=a_h)).json()
    assert cnt["count"] == 0


async def test_like_notification_deduped(client: AsyncClient, make_user):
    a_h, a_id = await make_user("nd_a@example.com", "ada2")
    b_h, _ = await make_user("nd_b@example.com", "ben2")
    pid = (await client.post("/api/posts", json={"text": "x"}, headers=a_h)).json()["id"]

    # Like / unlike / like again → still a single like notification.
    await client.post(f"/api/posts/{pid}/like", headers=b_h)
    await client.delete(f"/api/posts/{pid}/like", headers=b_h)
    await client.post(f"/api/posts/{pid}/like", headers=b_h)

    page = (await client.get("/api/notifications", headers=a_h)).json()
    likes = [n for n in page["notifications"] if n["type"] == "like"]
    assert len(likes) == 1


async def test_follow_request_notifications(client: AsyncClient, make_user):
    a_h, a_id = await make_user("nfr_a@example.com", "priv2")
    b_h, b_id = await make_user("nfr_b@example.com", "req2")
    await client.patch("/api/users/me", json={"is_private": True}, headers=a_h)

    await client.post(f"/api/users/{a_id}/follow", headers=b_h)  # request
    apage = (await client.get("/api/notifications", headers=a_h)).json()
    assert "follow_request" in {n["type"] for n in apage["notifications"]}

    await client.post(f"/api/users/me/follow-requests/{b_id}/accept", headers=a_h)
    bpage = (await client.get("/api/notifications", headers=b_h)).json()
    assert "follow_accept" in {n["type"] for n in bpage["notifications"]}
