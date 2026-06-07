# basic-agent · backend

FastAPI + LangChain backend that streams chat responses to the web frontend using the
AI SDK v5 UI Message Stream Protocol.

## Quick start

```bash
cd agent
cp .env.example .env   # fill in DASHSCOPE_API_KEY
uv sync
uv run uvicorn basic_agent.main:app --reload --port 8000
```

## Layout

- `core/`       – settings & logging
- `schemas/`    – Pydantic models aligned with AI SDK UIMessage
- `protocol/`   – AI SDK v5 UI Message Stream writer (SSE)
- `providers/`  – LLM provider abstraction (`DashScopeProvider` today)
- `agents/`     – Agent abstraction (`ChatAgent` today, future ReAct / tool-calling)
- `api/`        – FastAPI routes & dependency injection
- `tools/`      – Reserved for future tool implementations
- `memory/`     – Reserved for future conversation / vector memory

## Smoke test

```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"id":"t1","messages":[{"id":"u1","role":"user","parts":[{"type":"text","text":"你好"}]}]}'
```
