# basic-agent · web

React 18 + Vite + TypeScript + Tailwind + Zustand frontend.
Chat UI consumes the backend `/api/chat` endpoint via the AI SDK v5 `useChat` hook.

## Quick start

```bash
cd web
pnpm install
pnpm dev          # http://localhost:5173 (proxies /api -> http://localhost:8000)
```

The backend (`agent/`) must be running on port 8000 for chat to work.

## Scripts

| Command             | Purpose                       |
| ------------------- | ----------------------------- |
| `pnpm dev`          | Vite dev server (port 5173)   |
| `pnpm build`        | Type-check + production build |
| `pnpm preview`      | Preview the production build  |
| `pnpm typecheck`    | `tsc --noEmit` only           |
| `pnpm lint`         | ESLint                        |
| `pnpm lint:fix`     | ESLint with auto-fix          |
| `pnpm format`       | Prettier write                |
| `pnpm format:check` | Prettier check                |

A Husky `pre-commit` hook runs `lint-staged` (ESLint --fix + Prettier --write) on
changed `*.{ts,tsx,js,json,css,md,html}` files. The hook is installed automatically
by the `prepare` lifecycle script during `pnpm install`. **Requires the project
root to be a git repository.**

## Layout

- `pages/ChatPage.tsx` – single page
- `components/chat/` – ChatContainer / MessageList / MessageItem / MessageParts / ChatInput
- `services/chatTransport.ts` – DefaultChatTransport (single place to swap transports)
- `store/settingsStore.ts` – Zustand store (system prompt today; future sessions/tools)
- `lib/env.ts` – Vite env aggregation
- `eslint.config.js` – ESLint v9 flat config (TS + React + Prettier)
- `.prettierrc.json` / `.prettierignore` – Prettier config
- `scripts/husky-pre-commit.sh` – Hook template copied to `.husky/pre-commit` by `prepare`
