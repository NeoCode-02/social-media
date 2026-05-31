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
- **M3** Realtime (WebSocket + Redis pub/sub: live messages, typing, presence)
- **M4** Media in chat (presigned upload, thumbnails)
- **M5** Hardening (rate limits, logging, prod build) + seams for Twitter feed

See `~/.claude/plans/i-want-to-do-woolly-unicorn.md` for the full plan.
