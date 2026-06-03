from httpx import AsyncClient


async def test_edit_post_and_authz(client: AsyncClient, make_user):
    a_h, _ = await make_user("pe_a@example.com", "peditor")
    b_h, _ = await make_user("pe_b@example.com", "pother")

    pid = (await client.post("/api/posts", json={"text": "first draft"}, headers=a_h)).json()["id"]

    # Author edits → edited_at stamped.
    res = await client.patch(f"/api/posts/{pid}", json={"text": "final version"}, headers=a_h)
    assert res.status_code == 200
    body = res.json()
    assert body["text"] == "final version" and body["edited_at"] is not None

    # Non-author cannot edit.
    assert (
        await client.patch(f"/api/posts/{pid}", json={"text": "hijack"}, headers=b_h)
    ).status_code == 403


async def test_hashtags_search_trending(client: AsyncClient, make_user):
    h, _ = await make_user("ht@example.com", "tagger")

    p1 = (await client.post("/api/posts", json={"text": "go #climate go"}, headers=h)).json()["id"]
    await client.post("/api/posts", json={"text": "more #climate"}, headers=h)
    await client.post("/api/posts", json={"text": "unrelated #tech"}, headers=h)

    # Hashtag feed.
    climate = (await client.get("/api/posts/hashtag/climate?limit=50", headers=h)).json()
    assert len(climate["posts"]) == 2

    # Case-insensitive tag lookup.
    upper = (await client.get("/api/posts/hashtag/CLIMATE?limit=50", headers=h)).json()
    assert len(upper["posts"]) == 2

    # Trending ranks #climate (2) above #tech (1).
    trending = (await client.get("/api/posts/trending/hashtags", headers=h)).json()
    counts = {t["tag"]: t["count"] for t in trending}
    assert counts.get("climate") == 2 and counts.get("tech") == 1

    # Editing away the tag removes it from the feed.
    await client.patch(f"/api/posts/{p1}", json={"text": "no tags now"}, headers=h)
    climate2 = (await client.get("/api/posts/hashtag/climate?limit=50", headers=h)).json()
    assert len(climate2["posts"]) == 1

    # Full-text search.
    res = (await client.get("/api/posts/search?q=unrelated", headers=h)).json()
    assert len(res["posts"]) == 1 and "unrelated" in res["posts"][0]["text"]


async def test_lookup_user_by_username(client: AsyncClient, make_user):
    a_h, a_id = await make_user("lu@example.com", "lookupme")
    b_h, _ = await make_user("lu2@example.com", "viewer2")

    res = await client.get("/api/users/by-username/lookupme", headers=b_h)
    assert res.status_code == 200 and res.json()["id"] == a_id
    # Case-insensitive.
    assert (await client.get("/api/users/by-username/LookupMe", headers=b_h)).status_code == 200
    assert (await client.get("/api/users/by-username/ghost", headers=b_h)).status_code == 404
