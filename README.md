# social-media

Realtime chat + social platform (Telegram-style chat first, Twitter-style feed later).

## Stack

| Layer     | Tech                                                          |
| --------- | ------------------------------------------------------------ |
| Backend   | FastAPI · SQLAlchemy 2 (async) · Alembic · Pydantic v2       |
| Realtime  | WebSocket + Redis Pub/Sub fan-out                            |
| Data      | Postgres · Redis · MinIO (S3-compatible) · ARQ worker        |
| Frontend  | React 19 + Vite + TypeScript · TanStack Query · Zustand · Tailwind |
| Dev infra | Docker Compose (postgres, redis, minio, mailpit)            |

## Quick start

### 1. Infra (Postgres, Redis, MinIO, Mailpit)

```bash
docker compose up -d postgres redis minio minio-init mailpit
```

| Service      | URL / port                                   |
| ------------ | -------------------------------------------- |
| Postgres     | `localhost:5433` (postgres/postgres)         |
| Redis        | `localhost:6379`                             |
| MinIO API    | `localhost:9000` (minioadmin/minioadmin)     |
| MinIO console| http://localhost:9001                        |
| Mailpit UI   | http://localhost:8025 (SMTP `localhost:1025`)|

### 2. Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head      # apply migrations
uv run uvicorn app.main:app --reload
# health: http://localhost:8000/api/health
```

In a second terminal, run the background worker (sends verification emails, etc.):

```bash
cd backend && uv run arq app.worker.WorkerSettings
```

#### Auth API (M1)

| Method | Path                       | Purpose                                  |
| ------ | -------------------------- | ---------------------------------------- |
| POST   | `/api/auth/register`       | email + password; emails a 6-digit code  |
| POST   | `/api/auth/verify-email`   | confirm code → access token + refresh cookie |
| POST   | `/api/auth/resend-code`    | re-send verification code                |
| POST   | `/api/auth/login`          | password login (requires verified email) |
| POST   | `/api/auth/refresh`        | rotate refresh cookie → new access token |
| POST   | `/api/auth/logout`         | revoke refresh token                     |
| GET    | `/api/auth/google/login`   | Google OAuth (needs client id/secret)    |
| GET    | `/api/users/me`            | current profile (Bearer access token)    |
| PATCH  | `/api/users/me`            | update profile (bio/location/website/`is_private`) |
| POST   | `/api/users/me/avatar`     | multipart avatar upload → MinIO (≤25 MB) |
| GET    | `/api/users/{id}`          | a user's public profile (counts, follow/block state) |
| GET    | `/api/users/by-username/{username}` | resolve a `@handle` to a profile |

Access token (15 min) goes in the `Authorization: Bearer` header; the refresh token
(30 days, rotating) lives in an httpOnly cookie scoped to `/api/auth`. Verification
codes and the refresh-token allowlist live in Redis. Read the codes in dev from the
Mailpit UI (http://localhost:8025).

#### Chat API (M2)

| Method | Path                              | Purpose                                   |
| ------ | --------------------------------- | ----------------------------------------- |
| GET    | `/api/chats`                      | your chats + last message + unread count  |
| POST   | `/api/chats`                      | create a DM (`type:dm,user_id`) or group  |
| GET    | `/api/chats/{id}`                 | chat detail + members (must be a member)  |
| POST   | `/api/chats/{id}/members`         | add members to a group (owner/admin)      |
| DELETE | `/api/chats/{id}/members/me`      | leave a chat                              |
| POST   | `/api/chats/{id}/read`            | mark read up to a message id              |
| GET    | `/api/chats/{id}/messages`        | messages, newest-first (`limit`,`before`) |
| POST   | `/api/chats/{id}/messages`        | send a text message                       |
| PATCH  | `/api/messages/{id}`              | edit your message                         |
| DELETE | `/api/messages/{id}`              | soft-delete your message                  |
| POST   | `/api/chats/{id}/attachments`     | upload media (`as_file`/`is_voice`/`duration_ms`) |
| GET    | `/api/chats/{id}/attachments/{aid}/download-url` | signed link that forces a download |
| GET    | `/api/users/{id}`                 | another user's public profile (bio, etc.) |

Attachments cover images, video, audio, voice notes, and documents (≤15 MB). Images
open in an in-app lightbox; video/audio play inline; voice notes use a compact player;
anything else renders as a downloadable card. `as_file` forces the file card even for
images. DMs and groups only (channels are deferred). Messages use time-ordered **UUIDv7**
ids, so the id is also the chronological cursor; pagination and unread counts compare
ids directly. All chat endpoints require a verified email.

#### Realtime (M3)

Fetch a short-lived **ticket** from `GET /api/auth/ws-ticket` (Bearer access token),
then connect a WebSocket to `ws://localhost:8000/ws?ticket=<ticket>` (the vite dev
server proxies `/ws`). Messages are **sent over REST** and **received over the socket**;
typing and read receipts flow over the socket. Fan-out across API instances uses a single
Redis `psubscribe("user:*")` pattern listener — the publisher computes recipients and
publishes per-user, every process delivers to its locally connected sockets.

| Direction        | Event                                                   |
| ---------------- | ------------------------------------------------------- |
| server → client  | `message.new`, `message.edited`, `message.deleted`      |
| server → client  | `typing`, `message.read`, `presence` (online/offline)   |
| server → client  | `post.new` (a followee posted), `notification.new`      |
| client → server  | `typing.start` / `typing.stop` `{chat_id}`              |
| client → server  | `message.read` `{chat_id, last_read_message_id}`        |

Presence is tracked per process; `last_seen` is persisted on disconnect.

#### Social / feed API (Twitter half)

All require a verified email. Counts (like/reply/repost/view) are computed on read;
post ids are time-ordered **UUIDv7** cursors.

| Method | Path                                   | Purpose                                       |
| ------ | -------------------------------------- | --------------------------------------------- |
| GET    | `/api/posts`                           | home timeline (your + accepted-followees)     |
| GET    | `/api/posts/global`                    | global feed (everyone, block/mute filtered)   |
| POST   | `/api/posts`                           | create post / reply (`parent_id`) / quote     |
| GET    | `/api/posts/{id}`                      | one post (records a unique view)              |
| PATCH  | `/api/posts/{id}`                      | edit own post (stamps `edited_at`)            |
| DELETE | `/api/posts/{id}`                      | soft-delete own post                          |
| GET    | `/api/posts/{id}/replies`              | replies (cursor)                              |
| POST/DELETE | `/api/posts/{id}/like`            | like / unlike                                 |
| POST/DELETE | `/api/posts/{id}/repost`          | repost / undo                                 |
| GET    | `/api/posts/search?q=`                 | full-text post search (trigram-indexed)       |
| GET    | `/api/posts/hashtag/{tag}`             | posts for a hashtag                           |
| GET    | `/api/posts/trending/hashtags`         | trending tags (7-day window)                  |
| GET    | `/api/users/{id}/posts`                | a user's posts (private → 403 unless follower)|
| GET    | `/api/users/search?q=`                 | people search (block-filtered)                |
| POST/DELETE | `/api/users/{id}/follow`          | follow/request (private) / unfollow           |
| GET    | `/api/users/{id}/followers`·`/following` | accepted follower / following lists         |
| GET    | `/api/users/me/follow-requests`        | pending requests (private accounts)           |
| POST   | `/api/users/me/follow-requests/{id}/accept`·`/reject` | approve / decline a request    |
| POST/DELETE | `/api/users/{id}/block`           | block / unblock (mutual, severs follows)      |
| POST/DELETE | `/api/users/{id}/mute`            | mute / unmute (one-way feed hide)             |
| GET    | `/api/users/me/blocks`·`/mutes`        | manage blocked / muted accounts               |
| GET    | `/api/notifications`                   | notifications + `unread_count` (cursor)       |
| GET    | `/api/notifications/unread-count`      | unread badge count                            |
| POST   | `/api/notifications/read`              | mark read (all, or `{ids:[…]}`)               |

Notifications fire on like, reply, follow, follow-request, follow-accept and @mention
(self-actions skipped, like/follow deduped, suppressed across a block) and are pushed
live as `notification.new`. Hashtags (`#tag`) and mentions (`@user`) are parsed from
post text; mentions notify the mentioned user.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173 (proxies /api → :8000)
```

## Checks

```bash
# backend
cd backend && uv run ruff check . && uv run mypy app && uv run pytest -q
# frontend
cd frontend && npm run lint && npm run typecheck && npm run test && npm run build
```

## Roadmap (MVP = Telegram half)

- **M0** Scaffold & infra ✅
- **M1** Auth & users (email+password JWT, 6-digit verify, Google OAuth, avatars) ✅
- **M2** Chats & messages (DM/group, REST, cursor pagination, read receipts) ✅
- **M3** Realtime (WebSocket + Redis pub/sub: live messages, typing, presence) ✅
- **M4** Media in chat (images + files, MinIO storage, thumbnails) ✅
- **M5** Hardening (rate limits, structured logging + request IDs, security headers) ✅
- **Twitter half** Feed (posts, follows, likes, reposts, replies, timeline, profiles) ✅

Plus a full **React SPA** ("Pulse"): auth, chat list, live conversation (typing,
presence, read receipts), rich media (image lightbox, inline video/audio, voice
recording, file downloads), message edit/delete/reply, viewable user profiles with
bio/location/website, a profile editor with avatar cropping, and a public **feed**
(home timeline, composer, threaded replies, likes/reposts, follow graph).

## Hardening (M5)

- **Request IDs**: every response carries `X-Request-ID` (echoed if the client sends one);
  it appears in structured JSON logs and in 500 error bodies for tracing.
- **Structured logging**: one JSON line per request (`method`, `path`, `status`, `duration_ms`,
  `request_id`). Configure level via `DEBUG`.
- **Rate limits** (Redis fixed-window, per client IP): auth (login/register/resend),
  chat create, message send, attachment upload, user search, post create, post upload, follow.
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.
- **Global error handler**: unhandled exceptions → `500 {detail, request_id}` (logged with traceback).

## Deployment notes

For production, override these env vars (see `backend/.env.example`):
`SECRET_KEY` (strong random), `DEBUG=false`, `COOKIE_SECURE=true`, real `SMTP_*`,
`S3_*` (e.g. AWS S3), `GOOGLE_CLIENT_ID/SECRET`, and `CORS_ORIGINS`/`FRONTEND_URL`.
Build the API image from `backend/Dockerfile`; run `alembic upgrade head` on deploy;
run the API and a separate `arq app.worker.WorkerSettings` worker. Serve the frontend
`npm run build` output behind a CDN/static host with `/api` + `/ws` proxied to the API.

## Twitter half — feed, posts, follows

The public-feed half reuses the same auth, users, media, and realtime fan-out. Posts use
the same time-ordered **UUIDv7** ids/cursor as messages; like/reply/repost counts are
**computed on read** in batched queries (no denormalized-counter drift).

| Method | Path                              | Purpose                                   |
| ------ | --------------------------------- | ----------------------------------------- |
| GET    | `/api/posts`                      | home timeline (followees + you, cursor)   |
| POST   | `/api/posts`                      | create (`text`,`attachment_ids`,`parent_id`,`repost_of_id`) |
| GET    | `/api/posts/{id}`                 | single post (counts + your like/repost)   |
| DELETE | `/api/posts/{id}`                 | soft-delete your post                     |
| GET    | `/api/posts/{id}/replies`         | replies (cursor)                          |
| POST/DELETE | `/api/posts/{id}/like`       | like / unlike                             |
| POST/DELETE | `/api/posts/{id}/repost`     | repost / un-repost                        |
| POST   | `/api/posts/attachments`          | upload post media (reuses the chat pipeline) |
| GET    | `/api/users/{id}/posts`           | a user's profile feed                     |
| POST/DELETE | `/api/users/{id}/follow`     | follow / unfollow                         |
| GET    | `/api/users/{id}/followers` · `/following` | follow graph                     |

A reply is a post with `parent_id`; a repost is a post with `repost_of_id` (no text = bare
repost, with text = quote). New top-level posts publish `post.new` to the author's followers
over the per-user realtime channels, so open timelines update live.

The **SPA** adds an icon rail switching between **Home** (feed: composer, infinite timeline,
like/reply/repost, image/video/voice posts, threads) and **Messages** (the chat half), plus
profile pages with follow/unfollow and a user's posts.

### Later phases
Channels (broadcast chat) can reuse `posts` + `chats`; trending/hashtags, quote-post UI,
notifications, and mobile-responsive layout are still open.

See `~/.claude/plans/i-want-to-do-woolly-unicorn.md` for the full plan.
