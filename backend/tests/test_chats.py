from httpx import AsyncClient


async def test_dm_create_send_unread_read(
    client: AsyncClient, fake_redis, make_user
):
    a_h, _ = await make_user("a@example.com", "auser")
    b_h, b_id = await make_user("b@example.com", "buser")

    created = await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    assert created.status_code == 201
    chat = created.json()
    assert chat["type"] == "dm"
    assert len(chat["members"]) == 2
    chat_id = chat["id"]

    # DM creation is idempotent.
    again = await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    assert again.json()["id"] == chat_id

    msg = await client.post(
        f"/api/chats/{chat_id}/messages", json={"content": "hi B"}, headers=a_h
    )
    assert msg.status_code == 201
    assert msg.json()["content"] == "hi B"

    # B sees one unread.
    chats = (await client.get("/api/chats", headers=b_h)).json()
    assert len(chats) == 1
    assert chats[0]["unread_count"] == 1
    assert chats[0]["last_message"]["content"] == "hi B"

    # B reads up to the message → unread clears.
    read = await client.post(
        f"/api/chats/{chat_id}/read",
        json={"last_read_message_id": msg.json()["id"]},
        headers=b_h,
    )
    assert read.status_code == 204
    chats = (await client.get("/api/chats", headers=b_h)).json()
    assert chats[0]["unread_count"] == 0


async def test_non_member_blocked(client: AsyncClient, make_user):
    a_h, _ = await make_user("a@example.com", "auser")
    b_h, b_id = await make_user("b@example.com", "buser")
    c_h, _ = await make_user("c@example.com", "cuser")

    chat = (
        await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    ).json()
    cid = chat["id"]

    assert (await client.get(f"/api/chats/{cid}", headers=c_h)).status_code == 404
    sneak = await client.post(
        f"/api/chats/{cid}/messages", json={"content": "sneak"}, headers=c_h
    )
    assert sneak.status_code == 404


async def test_group_create_add_and_leave(client: AsyncClient, make_user):
    a_h, _ = await make_user("a@example.com", "auser")
    b_h, b_id = await make_user("b@example.com", "buser")
    c_h, c_id = await make_user("c@example.com", "cuser")

    group = await client.post(
        "/api/chats",
        json={"type": "group", "title": "Squad", "member_ids": [b_id]},
        headers=a_h,
    )
    assert group.status_code == 201
    assert group.json()["title"] == "Squad"
    assert len(group.json()["members"]) == 2
    gid = group.json()["id"]

    # Non-admin member cannot add.
    denied = await client.post(
        f"/api/chats/{gid}/members", json={"user_ids": [c_id]}, headers=b_h
    )
    assert denied.status_code == 403

    # Owner adds C.
    added = await client.post(
        f"/api/chats/{gid}/members", json={"user_ids": [c_id]}, headers=a_h
    )
    assert added.status_code == 200
    assert len(added.json()["members"]) == 3

    # C leaves.
    left = await client.delete(f"/api/chats/{gid}/members/me", headers=c_h)
    assert left.status_code == 204
    assert (await client.get(f"/api/chats/{gid}", headers=c_h)).status_code == 404


async def test_edit_and_delete_message(client: AsyncClient, make_user):
    a_h, _ = await make_user("a@example.com", "auser")
    b_h, b_id = await make_user("b@example.com", "buser")
    chat = (
        await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    ).json()
    mid = (
        await client.post(
            f"/api/chats/{chat['id']}/messages", json={"content": "orig"}, headers=a_h
        )
    ).json()["id"]

    edited = await client.patch(f"/api/messages/{mid}", json={"content": "edited"}, headers=a_h)
    assert edited.status_code == 200
    assert edited.json()["content"] == "edited"
    assert edited.json()["edited_at"] is not None

    # B cannot edit A's message.
    assert (
        await client.patch(f"/api/messages/{mid}", json={"content": "hack"}, headers=b_h)
    ).status_code == 403

    deleted = await client.delete(f"/api/messages/{mid}", headers=a_h)
    assert deleted.status_code == 200
    assert deleted.json()["deleted_at"] is not None
    assert deleted.json()["content"] is None


async def test_message_pagination_is_ordered(client: AsyncClient, make_user):
    a_h, _ = await make_user("a@example.com", "auser")
    b_h, b_id = await make_user("b@example.com", "buser")
    cid = (
        await client.post("/api/chats", json={"type": "dm", "user_id": b_id}, headers=a_h)
    ).json()["id"]

    for i in range(5):
        await client.post(
            f"/api/chats/{cid}/messages", json={"content": f"m{i}"}, headers=a_h
        )

    page1 = (await client.get(f"/api/chats/{cid}/messages?limit=2", headers=a_h)).json()
    assert [m["content"] for m in page1["messages"]] == ["m4", "m3"]
    assert page1["next_cursor"] is not None

    page2 = (
        await client.get(
            f"/api/chats/{cid}/messages?limit=2&before={page1['next_cursor']}", headers=a_h
        )
    ).json()
    assert [m["content"] for m in page2["messages"]] == ["m2", "m1"]
