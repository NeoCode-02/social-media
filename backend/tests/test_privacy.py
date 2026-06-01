from httpx import AsyncClient

from tests.test_posts import _make_user


async def test_private_account_follow_request_flow(client: AsyncClient, fake_redis):
    pat_h, pat_id = await _make_user(client, fake_redis, "pat@example.com", "pat")
    quinn_h, quinn_id = await _make_user(client, fake_redis, "quinn@example.com", "quinn")

    post = await client.post("/api/posts", json={"text": "secret"}, headers=pat_h)
    pid = post.json()["id"]

    # Pat goes private.
    assert (
        await client.patch("/api/users/me", json={"is_private": True}, headers=pat_h)
    ).status_code == 200

    # Outsider sees a locked profile (no posts, no bio).
    prof = (await client.get(f"/api/users/{pat_id}", headers=quinn_h)).json()
    assert prof["is_private"] and not prof["can_view_posts"]
    assert prof["follow_state"] == "none" and prof["bio"] is None

    # Following a private account is a request, not an instant follow.
    res = await client.post(f"/api/users/{pat_id}/follow", headers=quinn_h)
    assert res.status_code == 200 and res.json()["status"] == "pending"
    assert (await client.get(f"/api/users/{pat_id}/posts", headers=quinn_h)).status_code == 403

    # Pat sees the pending request + counter.
    reqs = (await client.get("/api/users/me/follow-requests", headers=pat_h)).json()
    assert [u["username"] for u in reqs] == ["quinn"]
    assert (await client.get("/api/users/me", headers=pat_h)).json()["pending_requests"] == 1

    # Pat accepts → Quinn gains access.
    assert (
        await client.post(
            f"/api/users/me/follow-requests/{quinn_id}/accept", headers=pat_h
        )
    ).status_code == 204
    feed = await client.get(f"/api/users/{pat_id}/posts", headers=quinn_h)
    assert feed.status_code == 200 and feed.json()["posts"][0]["id"] == pid
    prof = (await client.get(f"/api/users/{pat_id}", headers=quinn_h)).json()
    assert prof["follow_state"] == "accepted" and prof["is_following"]
    assert prof["followers_count"] == 1


async def test_reject_follow_request(client: AsyncClient, fake_redis):
    a_h, a_id = await _make_user(client, fake_redis, "ra@example.com", "ralph")
    b_h, b_id = await _make_user(client, fake_redis, "rb@example.com", "rita")
    await client.patch("/api/users/me", json={"is_private": True}, headers=a_h)

    await client.post(f"/api/users/{a_id}/follow", headers=b_h)
    assert (
        await client.post(
            f"/api/users/me/follow-requests/{b_id}/reject", headers=a_h
        )
    ).status_code == 204
    # Gone from the inbox; B still has no access.
    assert (await client.get("/api/users/me/follow-requests", headers=a_h)).json() == []
    prof = (await client.get(f"/api/users/{a_id}", headers=b_h)).json()
    assert prof["follow_state"] == "none" and not prof["can_view_posts"]


async def test_post_view_count_dedups(client: AsyncClient, fake_redis):
    a_h, _ = await _make_user(client, fake_redis, "va@example.com", "vicky")
    b_h, _ = await _make_user(client, fake_redis, "vb@example.com", "vince")
    pid = (await client.post("/api/posts", json={"text": "viewed"}, headers=a_h)).json()["id"]

    for _ in range(3):  # B opens 3 times = 1 unique view
        await client.get(f"/api/posts/{pid}", headers=b_h)
    await client.get(f"/api/posts/{pid}", headers=a_h)  # author view = +1
    final = (await client.get(f"/api/posts/{pid}", headers=b_h)).json()
    assert final["view_count"] == 2
