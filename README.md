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
| PATCH  | `/api/users/me`            | update display name / avatar             |
| POST   | `/api/users/me/avatar-url` | presigned MinIO URL for direct upload    |

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

DMs and groups only (channels are deferred). Messages use time-ordered **UUIDv7**
ids, so the id is also the chronological cursor; pagination and unread counts compare
ids directly. All chat endpoints require a verified email.

#### Realtime (M3)

Connect a WebSocket to `ws://localhost:8000/ws?token=<access_token>` (the vite dev
server proxies `/ws`). Messages are **sent over REST** and **received over the socket**;
typing and read receipts flow over the socket. Fan-out across API instances uses Redis
pub/sub — the publisher computes recipients, every process delivers to its locally
connected sockets.

| Direction        | Event                                                   |
| ---------------- | ------------------------------------------------------- |
| server → client  | `message.new`, `message.edited`, `message.deleted`      |
| server → client  | `typing`, `message.read`, `presence` (online/offline)   |
| client → server  | `typing.start` / `typing.stop` `{chat_id}`              |
| client → server  | `message.read` `{chat_id, last_read_message_id}`        |

Presence is tracked per process; `last_seen` is persisted on disconnect.

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

Plus a full **React SPA** ("Pulse"): auth, chat list, live conversation (typing,
presence, read receipts), media, message edit/delete, profile editor.

## Hardening (M5)

- **Request IDs**: every response carries `X-Request-ID` (echoed if the client sends one);
  it appears in structured JSON logs and in 500 error bodies for tracing.
- **Structured logging**: one JSON line per request (`method`, `path`, `status`, `duration_ms`,
  `request_id`). Configure level via `DEBUG`.
- **Rate limits** (Redis fixed-window, per client IP): auth (login/register/resend),
  chat create, message send, attachment upload, user search.
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.
- **Global error handler**: unhandled exceptions → `500 {detail, request_id}` (logged with traceback).

## Deployment notes

For production, override these env vars (see `backend/.env.example`):
`SECRET_KEY` (strong random), `DEBUG=false`, `COOKIE_SECURE=true`, real `SMTP_*`,
`S3_*` (e.g. AWS S3), `GOOGLE_CLIENT_ID/SECRET`, and `CORS_ORIGINS`/`FRONTEND_URL`.
Build the API image from `backend/Dockerfile`; run `alembic upgrade head` on deploy;
run the API and a separate `arq app.worker.WorkerSettings` worker. Serve the frontend
`npm run build` output behind a CDN/static host with `/api` + `/ws` proxied to the API.

## Next phase — Twitter feed (seams)

The chat MVP is the Telegram half. The public-feed half slots in as new modules without
touching chat, reusing the same auth, users, media, and realtime fan-out:

- `modules/posts` — `posts` table (author, text, attachments via existing `attachments`),
  create/delete, `POST/GET /api/posts`.
- `modules/follows` — `follows` (follower_id, followee_id); follow/unfollow + counts.
- `modules/timeline` — home timeline (fan-out-on-read first: posts from followees, cursor
  paginated by UUIDv7 id like messages), plus per-user profile feed.
- `modules/interactions` — likes / reposts / replies (reply = post with `parent_id`).
- Realtime: publish `post.new` / `like` over the existing Redis channel to live-update feeds.
- Channels (broadcast chat) can reuse `posts` + `chats` once the feed exists.

See `~/.claude/plans/i-want-to-do-woolly-unicorn.md` for the full plan.
