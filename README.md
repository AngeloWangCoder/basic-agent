# basic-agent

Monorepo for a Claude-Code-style agent prototype.

- **`agent/`** — Python (FastAPI + LangChain) backend. Streams responses using AI SDK v5 UI Message Stream Protocol. Uses `uv`.
- **`web/`**   — React 18 + Vite + TypeScript + Tailwind + Zustand frontend. Uses `@ai-sdk/react` (`useChat`). Uses `pnpm`.

## Stage 1: basic chat

Get the two services up:

```bash
# terminal A — backend
cd agent
cp .env.example .env   # fill DASHSCOPE_API_KEY
uv sync
uv run uvicorn basic_agent.main:app --reload --port 8000

# terminal B — frontend
cd web
pnpm install
pnpm dev               # http://localhost:5173
```

Vite proxies `/api` → `http://localhost:8000`, so no CORS hassle in dev.

See `agent/README.md` and `web/README.md` for details. Stage-by-stage design & delivery docs live in [`docs/`](./docs/).

## Stage docs

- [Stage 01 · 基础聊天 + 可扩展架构](./docs/stage-01-basic-chat.md)

> 工作流：每个新阶段开始前先生成 `docs/stage-XX-*.md` 计划文档 → 输出审阅 → 通过后再编码。
