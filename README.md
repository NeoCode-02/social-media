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
- **M1** Auth & users (email+password JWT, 6-digit verify, Google OAuth, avatars)
- **M2** Chats & messages (DM/group, REST, cursor pagination, read receipts)
- **M3** Realtime (WebSocket + Redis pub/sub: live messages, typing, presence)
- **M4** Media in chat (presigned upload, thumbnails)
- **M5** Hardening (rate limits, logging, prod build) + seams for Twitter feed

See `~/.claude/plans/i-want-to-do-woolly-unicorn.md` for the full plan.
