"""Private-account post visibility across every read path.

Regression coverage for the leak where `can_view_posts` was only enforced on
the profile feed, so private posts surfaced via the global feed, search,
hashtags, single-post GET and replies — and a blocked user could still read a
post by id.
"""
from httpx import AsyncClient


async def _global_ids(client: AsyncClient, headers) -> set[str]:
    page = (await client.get("/api/posts/global?limit=50", headers=headers)).json()
    return {p["id"] for p in page["posts"]}


async def test_private_posts_hidden_from_every_discovery_surface(client: AsyncClient, make_user):
    pat_h, pat_id = await make_user("pv_pat@example.com", "patpriv")
    out_h, _ = await make_user("pv_out@example.com", "outsider")

    pid = (
        await client.post(
            "/api/posts", json={"text": "topsecret #classified"}, headers=pat_h
        )
    ).json()["id"]
    assert (
        await client.patch("/api/users/me", json={"is_private": True}, headers=pat_h)
    ).status_code == 200

    # Outsider can't reach it any way.
    assert pid not in await _global_ids(client, out_h)
    assert (await client.get("/api/posts/search?q=topsecret", headers=out_h)).json()["posts"] == []
    assert (
        await client.get("/api/posts/hashtag/classified", headers=out_h)
    ).json()["posts"] == []
    assert (await client.get(f"/api/posts/{pid}", headers=out_h)).status_code == 403
    assert (await client.get(f"/api/posts/{pid}/replies", headers=out_h)).status_code == 403

    # The owner still sees their own post everywhere.
    assert pid in await _global_ids(client, pat_h)
    assert (await client.get(f"/api/posts/{pid}", headers=pat_h)).status_code == 200
    assert len(
        (await client.get("/api/posts/search?q=topsecret", headers=pat_h)).json()["posts"]
    ) == 1


async def test_accepted_follower_regains_access(client: AsyncClient, make_user):
    pat_h, pat_id = await make_user("pv2_pat@example.com", "pat2priv")
    fan_h, fan_id = await make_user("pv2_fan@example.com", "fan2")

    pid = (
        await client.post("/api/posts", json={"text": "members only #vip"}, headers=pat_h)
    ).json()["id"]
    await client.patch("/api/users/me", json={"is_private": True}, headers=pat_h)

    # A pending request grants nothing.
    await client.post(f"/api/users/{pat_id}/follow", headers=fan_h)
    assert pid not in await _global_ids(client, fan_h)
    assert (await client.get(f"/api/posts/{pid}", headers=fan_h)).status_code == 403

    # Acceptance opens every surface.
    await client.post(f"/api/users/me/follow-requests/{fan_id}/accept", headers=pat_h)
    assert pid in await _global_ids(client, fan_h)
    assert (await client.get(f"/api/posts/{pid}", headers=fan_h)).status_code == 200
    assert len((await client.get("/api/posts/hashtag/vip", headers=fan_h)).json()["posts"]) == 1
    assert len(
        (await client.get("/api/posts/search?q=members", headers=fan_h)).json()["posts"]
    ) == 1


async def test_blocked_user_cannot_read_post_by_id(client: AsyncClient, make_user):
    a_h, _ = await make_user("pv3_a@example.com", "pv3a")
    b_h, b_id = await make_user("pv3_b@example.com", "pv3b")

    pid = (await client.post("/api/posts", json={"text": "public post"}, headers=a_h)).json()["id"]
    assert (await client.get(f"/api/posts/{pid}", headers=b_h)).status_code == 200  # before block

    assert (await client.post(f"/api/users/{b_id}/block", headers=a_h)).status_code == 204
    assert (await client.get(f"/api/posts/{pid}", headers=b_h)).status_code == 403  # after block


async def test_private_followers_following_lists_gated(client: AsyncClient, make_user):
    pat_h, pat_id = await make_user("pv4_pat@example.com", "pat4")
    out_h, out_id = await make_user("pv4_out@example.com", "out4")
    await client.patch("/api/users/me", json={"is_private": True}, headers=pat_h)

    # Outsider can't enumerate a private account's social graph.
    assert (await client.get(f"/api/users/{pat_id}/followers", headers=out_h)).status_code == 403
    assert (await client.get(f"/api/users/{pat_id}/following", headers=out_h)).status_code == 403
    # The owner always can.
    assert (await client.get(f"/api/users/{pat_id}/followers", headers=pat_h)).status_code == 200

    # An accepted follower can.
    await client.post(f"/api/users/{pat_id}/follow", headers=out_h)
    await client.post(f"/api/users/me/follow-requests/{out_id}/accept", headers=pat_h)
    assert (await client.get(f"/api/users/{pat_id}/followers", headers=out_h)).status_code == 200


async def test_public_followers_following_still_open(client: AsyncClient, make_user):
    """A public account's follower/following lists stay visible to anyone."""
    a_h, a_id = await make_user("pv5_a@example.com", "pv5a")
    b_h, b_id = await make_user("pv5_b@example.com", "pv5b")
    await client.post(f"/api/users/{a_id}/follow", headers=b_h)

    followers = (await client.get(f"/api/users/{a_id}/followers", headers=b_h)).json()
    assert b_id in [u["id"] for u in followers]
