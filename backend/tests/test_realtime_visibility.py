"""`post.new` fan-out reaches accepted followers (and the author) only — never a
pending follower of a private account."""
import uuid
from datetime import UTC, datetime

from app.modules.follows.models import ACCEPTED, PENDING, Follow
from app.modules.posts.schemas import PostRead
from app.modules.realtime.events import publish_post_new
from app.modules.users.schemas import UserPublic


async def test_post_new_skips_pending_followers(db_sessionmaker, fake_redis):
    author = uuid.uuid4()
    accepted = uuid.uuid4()
    pending = uuid.uuid4()

    async with db_sessionmaker() as db:
        db.add_all(
            [
                Follow(follower_id=accepted, followee_id=author, status=ACCEPTED),
                Follow(follower_id=pending, followee_id=author, status=PENDING),
            ]
        )
        await db.commit()

        subs = {}
        for uid in (author, accepted, pending):
            ps = fake_redis.pubsub()
            await ps.subscribe(f"user:{uid}")
            await ps.get_message(timeout=1)  # consume the subscribe ack
            subs[uid] = ps

        post = PostRead(
            id=uuid.uuid4(),
            author=UserPublic(id=author, username="auth", display_name="Auth", avatar_url=None),
            text="hello followers",
            parent_id=None,
            created_at=datetime.now(UTC),
            edited_at=None,
            deleted_at=None,
        )
        await publish_post_new(db, post)

    # Author + accepted follower receive the envelope; the pending follower does not.
    assert (await subs[author].get_message(timeout=1)) is not None
    assert (await subs[accepted].get_message(timeout=1)) is not None
    assert (await subs[pending].get_message(timeout=1)) is None

    for ps in subs.values():
        await ps.aclose()
