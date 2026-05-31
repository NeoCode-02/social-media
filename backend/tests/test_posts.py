from httpx import AsyncClient

import app.modules.messages.service as msg_service
import app.modules.posts.router as posts_router


async def _make_user(
    client: AsyncClient, fake_redis, email: str, username: str
) -> tuple[dict[str, str], str]:
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


async def test_create_get_delete_post(client: AsyncClient, fake_redis):
    h, uid = await _make_user(client, fake_redis, "a@example.com", "auser")
    created = await client.post("/api/posts", json={"text": "hello feed"}, headers=h)
    assert created.status_code == 201
    post = created.json()
    assert post["text"] == "hello feed"
    assert post["like_count"] == 0 and post["reply_count"] == 0
    pid = post["id"]

    got = await client.get(f"/api/posts/{pid}", headers=h)
    assert got.status_code == 200 and got.json()["author"]["id"] == uid

    # empty post rejected
    bad = await client.post("/api/posts", json={}, headers=h)
    assert bad.status_code == 422

    deleted = await client.delete(f"/api/posts/{pid}", headers=h)
    assert deleted.status_code == 200 and deleted.json()["deleted_at"]
    assert (await client.get(f"/api/posts/{pid}", headers=h)).status_code == 404


async def test_delete_others_post_forbidden(client: AsyncClient, fake_redis):
    a_h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")
    b_h, _ = await _make_user(client, fake_redis, "b@example.com", "buser")
    pid = (await client.post("/api/posts", json={"text": "mine"}, headers=a_h)).json()["id"]
    assert (await client.delete(f"/api/posts/{pid}", headers=b_h)).status_code == 403


async def test_timeline_follow_gating(client: AsyncClient, fake_redis):
    a_h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")
    b_h, b_id = await _make_user(client, fake_redis, "b@example.com", "buser")
    c_h, c_id = await _make_user(client, fake_redis, "c@example.com", "cuser")

    await client.post("/api/posts", json={"text": "from B"}, headers=b_h)
    await client.post("/api/posts", json={"text": "from C"}, headers=c_h)
    await client.post("/api/posts", json={"text": "from A"}, headers=a_h)

    # A follows only B → sees B + own A, not C
    assert (await client.post(f"/api/users/{b_id}/follow", headers=a_h)).status_code == 204
    feed = (await client.get("/api/posts", headers=a_h)).json()["posts"]
    texts = [p["text"] for p in feed]
    assert "from B" in texts and "from A" in texts and "from C" not in texts

    # unfollow → B drops out
    assert (await client.delete(f"/api/users/{b_id}/follow", headers=a_h)).status_code == 204
    texts2 = [p["text"] for p in (await client.get("/api/posts", headers=a_h)).json()["posts"]]
    assert "from B" not in texts2 and "from A" in texts2
    assert c_id  # silence unused


async def test_like_unlike(client: AsyncClient, fake_redis):
    a_h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")
    b_h, _ = await _make_user(client, fake_redis, "b@example.com", "buser")
    pid = (await client.post("/api/posts", json={"text": "like me"}, headers=a_h)).json()["id"]

    assert (await client.post(f"/api/posts/{pid}/like", headers=b_h)).status_code == 204
    # idempotent
    await client.post(f"/api/posts/{pid}/like", headers=b_h)
    seen = (await client.get(f"/api/posts/{pid}", headers=b_h)).json()
    assert seen["like_count"] == 1 and seen["liked_by_me"] is True
    # author sees the count but not liked_by_me
    author_view = (await client.get(f"/api/posts/{pid}", headers=a_h)).json()
    assert author_view["like_count"] == 1 and author_view["liked_by_me"] is False

    assert (await client.delete(f"/api/posts/{pid}/like", headers=b_h)).status_code == 204
    after = (await client.get(f"/api/posts/{pid}", headers=b_h)).json()
    assert after["like_count"] == 0 and after["liked_by_me"] is False


async def test_replies(client: AsyncClient, fake_redis):
    a_h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")
    b_h, _ = await _make_user(client, fake_redis, "b@example.com", "buser")
    pid = (await client.post("/api/posts", json={"text": "parent"}, headers=a_h)).json()["id"]

    r = await client.post(
        "/api/posts", json={"text": "a reply", "parent_id": pid}, headers=b_h
    )
    assert r.status_code == 201
    assert r.json()["reply_to"]["id"] == pid

    parent = (await client.get(f"/api/posts/{pid}", headers=a_h)).json()
    assert parent["reply_count"] == 1

    replies = (await client.get(f"/api/posts/{pid}/replies", headers=a_h)).json()["posts"]
    assert [p["text"] for p in replies] == ["a reply"]

    # replies are excluded from the home timeline
    own = [p["text"] for p in (await client.get("/api/posts", headers=b_h)).json()["posts"]]
    assert "a reply" not in own


async def test_repost(client: AsyncClient, fake_redis):
    a_h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")
    b_h, b_id = await _make_user(client, fake_redis, "b@example.com", "buser")
    pid = (await client.post("/api/posts", json={"text": "repost me"}, headers=a_h)).json()["id"]

    assert (await client.post(f"/api/posts/{pid}/repost", headers=b_h)).status_code == 204
    src = (await client.get(f"/api/posts/{pid}", headers=b_h)).json()
    assert src["repost_count"] == 1 and src["reposted_by_me"] is True

    # repost shows on B's profile feed, embedding the original
    feed = (await client.get(f"/api/users/{b_id}/posts", headers=b_h)).json()["posts"]
    assert any(p.get("repost_of") and p["repost_of"]["text"] == "repost me" for p in feed)

    assert (await client.delete(f"/api/posts/{pid}/repost", headers=b_h)).status_code == 204
    after = (await client.get(f"/api/posts/{pid}", headers=b_h)).json()
    assert after["repost_count"] == 0 and after["reposted_by_me"] is False


async def test_follow_rules_and_profile_counts(client: AsyncClient, fake_redis):
    a_h, a_id = await _make_user(client, fake_redis, "a@example.com", "auser")
    b_h, b_id = await _make_user(client, fake_redis, "b@example.com", "buser")

    assert (await client.post(f"/api/users/{a_id}/follow", headers=a_h)).status_code == 400  # self
    assert (
        await client.post(
            "/api/users/00000000-0000-0000-0000-000000000000/follow", headers=a_h
        )
    ).status_code == 404

    await client.post(f"/api/users/{b_id}/follow", headers=a_h)
    await client.post("/api/posts", json={"text": "p1"}, headers=b_h)
    await client.post("/api/posts", json={"text": "p2"}, headers=b_h)

    prof = (await client.get(f"/api/users/{b_id}", headers=a_h)).json()
    assert prof["followers_count"] == 1
    assert prof["posts_count"] == 2
    assert prof["is_following"] is True

    followers = (await client.get(f"/api/users/{b_id}/followers", headers=a_h)).json()
    assert a_id in [u["id"] for u in followers]
    following = (await client.get(f"/api/users/{a_id}/following", headers=a_h)).json()
    assert b_id in [u["id"] for u in following]


async def test_post_attachment_and_download(client: AsyncClient, fake_redis, monkeypatch):
    monkeypatch.setattr(msg_service, "put_object", lambda *a, **k: None)
    monkeypatch.setattr(
        posts_router, "presigned_get_url", lambda key, name=None: f"http://signed/{key}"
    )
    h, _ = await _make_user(client, fake_redis, "a@example.com", "auser")

    up = await client.post(
        "/api/posts/attachments",
        files={"file": ("clip.mp4", b"fake video", "video/mp4")},
        headers=h,
    )
    assert up.status_code == 201
    aid = up.json()["id"]

    post = await client.post(
        "/api/posts", json={"text": "with video", "attachment_ids": [aid]}, headers=h
    )
    assert post.status_code == 201
    assert post.json()["attachments"][0]["mime"] == "video/mp4"

    # reusing the same loose attachment again must fail
    again = await client.post(
        "/api/posts", json={"text": "again", "attachment_ids": [aid]}, headers=h
    )
    assert again.status_code == 400

    dl = await client.get(f"/api/posts/attachments/{aid}/download-url", headers=h)
    assert dl.status_code == 200 and dl.json()["url"].startswith("http")
