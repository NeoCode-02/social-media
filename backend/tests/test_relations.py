from httpx import AsyncClient

from tests.test_posts import _make_user


async def _global_ids(client: AsyncClient, headers) -> set[str]:
    page = (await client.get("/api/posts/global?limit=50", headers=headers)).json()
    return {p["id"] for p in page["posts"]}


async def test_block_is_bidirectional_and_guards(client: AsyncClient, fake_redis):
    a_h, a_id = await _make_user(client, fake_redis, "bl_a@example.com", "blocka")
    b_h, b_id = await _make_user(client, fake_redis, "bl_b@example.com", "blockb")
    pa = (await client.post("/api/posts", json={"text": "A post"}, headers=a_h)).json()["id"]
    pb = (await client.post("/api/posts", json={"text": "B post"}, headers=b_h)).json()["id"]

    assert (await client.post(f"/api/users/{b_id}/block", headers=a_h)).status_code == 204

    # Neither sees the other's posts in the global feed.
    assert pb not in await _global_ids(client, a_h)
    assert pa not in await _global_ids(client, b_h)

    # Blocked party gets 403 on the blocker's profile; blocker still sees it (locked).
    assert (await client.get(f"/api/users/{a_id}", headers=b_h)).status_code == 403
    prof = (await client.get(f"/api/users/{b_id}", headers=a_h)).json()
    assert prof["is_blocked"] and not prof["can_view_posts"]

    # Interactions blocked.
    assert (await client.get(f"/api/users/{b_id}/posts", headers=a_h)).status_code == 403
    assert (await client.post(f"/api/posts/{pa}/like", headers=b_h)).status_code == 403
    assert (await client.post(f"/api/users/{a_id}/follow", headers=b_h)).status_code == 403
    assert (
        await client.post("/api/posts", json={"text": "x", "parent_id": pa}, headers=b_h)
    ).status_code == 403

    # Hidden from search; present in blocks list.
    found = (await client.get("/api/users/search?q=blockb", headers=a_h)).json()
    assert all(u["id"] != b_id for u in found)
    blocks = (await client.get("/api/users/me/blocks", headers=a_h)).json()
    assert [u["id"] for u in blocks] == [b_id]

    # Unblock restores visibility.
    assert (await client.delete(f"/api/users/{b_id}/block", headers=a_h)).status_code == 204
    assert pb in await _global_ids(client, a_h)


async def test_mute_hides_feed_one_way(client: AsyncClient, fake_redis):
    a_h, a_id = await _make_user(client, fake_redis, "mu_a@example.com", "mutea")
    c_h, c_id = await _make_user(client, fake_redis, "mu_c@example.com", "mutec")
    pa = (await client.post("/api/posts", json={"text": "A post"}, headers=a_h)).json()["id"]
    pc = (await client.post("/api/posts", json={"text": "C post"}, headers=c_h)).json()["id"]

    assert (await client.post(f"/api/users/{c_id}/mute", headers=a_h)).status_code == 204
    assert pc not in await _global_ids(client, a_h)  # hidden from muter
    assert pa in await _global_ids(client, c_h)  # mute is one-way

    # Mute does not block viewing the profile or its posts.
    prof = await client.get(f"/api/users/{c_id}", headers=a_h)
    assert prof.status_code == 200 and prof.json()["is_muted"]
    assert (await client.get(f"/api/users/{c_id}/posts", headers=a_h)).status_code == 200

    mutes = (await client.get("/api/users/me/mutes", headers=a_h)).json()
    assert [u["id"] for u in mutes] == [c_id]

    assert (await client.delete(f"/api/users/{c_id}/mute", headers=a_h)).status_code == 204
    assert pc in await _global_ids(client, a_h)
