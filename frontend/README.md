# Frontend (React 19 + Vite + TanStack Query)

## Scripts

| Command            | What it does                                       |
| ------------------ | -------------------------------------------------- |
| `npm run dev`      | Vite dev server with HMR, proxies `/api` → backend |
| `npm run build`    | Type-check + production build to `dist/`           |
| `npm run preview`  | Serve the built bundle locally                     |
| `npm run test`     | Vitest run (jsdom environment)                     |
| `npm run lint`     | ESLint                                             |
| `npm run typecheck`| `tsc -b --noEmit`                                  |

## Environment

The dev server reads `VITE_API_BASE` (default: empty, calls go to the Vite
proxy). For production builds, set it to the absolute origin of the API.

```bash
# .env.local
VITE_API_BASE=https://api.example.com
```

## Proxy

`vite.config.ts` proxies `/api` and `/uploads` to `http://localhost:8000`.
The dev server runs on port `5173` by default; the backend must be listening
on `8000` (or update the proxy target).

## Testing

Vitest uses jsdom + React Testing Library. Mock the API layer with
`vi.mock('@/api/...')` rather than reaching into fetch — see
`src/features/chat/Conversation.test.tsx` for the canonical pattern.

## Structure

```
src/
  api/         # typed axios wrappers
  components/  # design-system primitives + shared widgets
  features/    # feature folders: feed, chat, profile, …
  lib/         # linkify, error, upload, utils
  pages/       # auth pages
  realtime/    # WebSocket client + event fan-out
  store/       # zustand stores (auth, realtime)
```

## Conventions

- Use `@/` path alias (resolves to `src/`).
- No `any` unless wrapping a third-party type; prefer `unknown` + a guard.
- React 19 + TypeScript strict mode. New components must be typed.
- Co-locate tests as `*.test.ts(x)` next to the file they cover.
