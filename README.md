# basic-agent

> 一个**类 Claude Code 的全栈智能体（Agent）原型**：React 聊天前端 ↔ FastAPI + LangChain 后端 ↔ 阿里云百炼大模型，通过 **AI SDK v5 UI Message Stream Protocol** 实现端到端流式对话。
>
> 项目刻意保持「最小可用闭环」，但所有核心模块（Provider / Agent / 协议 / 消息渲染）都做了抽象与扩展点，便于在其上继续开发工具调用、多轮记忆、ReAct/Plan-Execute 等能力，而不必推翻重来。

---

## ✨ 功能特性

- 💬 **流式聊天**：用户输入 → 大模型逐字（token-by-token）流式回复，气泡实时显现。
- 🌊 **标准协议**：后端输出 AI SDK v5 UI Message Stream（SSE / JSON 事件），前端 `useChat` 零配置消费。
- 🧱 **可扩展架构**：Provider（换模型）、Agent（换推理策略）、Protocol（加事件类型）、Message Parts（加渲染类型）四层均可独立扩展。
- 🌍 **多轮对话**：兼容 AI SDK v5 在历史消息里回传的 `step-start` / `tool-*` 等元数据 part。
- 🛠️ **前端工程化**：ESLint 9 (flat config) + Prettier 3 + Husky + lint-staged 全套，提交即自动格式化/校验。
- 🔌 **开发友好**：Vite 代理 `/api` → 后端，开发期无 CORS 烦恼；`uv` / `pnpm` 极速依赖管理。

---

## 🏗️ 架构总览

整体是一个 monorepo，分前端 `web/` 与后端 `agent/` 两个独立服务，开发期由 Vite 代理打通：

```
┌─────────────────────────────────────────────────────────────────────┐
│  浏览器  ── React 18 + @ai-sdk/react useChat                          │
│             ChatPage → ChatContainer(useChat) → MessageList           │
│                         → MessageItem → MessageParts → TextPart       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  POST /api/chat
                                │  { id, messages: UIMessage[] }
                                ▼
                   Vite Dev Server  :5173
                                │  proxy  /api  ──▶  http://localhost:8000
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI  :8000   (agent/src/basic_agent)                             │
│                                                                       │
│  api/routes/chat.py   POST /api/chat                                  │
│     │  1. 解析 ChatRequest (schemas/chat.py)                          │
│     │  2. get_chat_agent()  (api/deps.py, lru_cache 单例)             │
│     │  3. 创建 UIStreamWriter，后台 task 跑 agent，立刻返回流          │
│     ▼                                                                 │
│  agents/chat_agent.py   ChatAgent.stream(messages, writer)            │
│     │  · UIMessage → LangChain Human/AI/System Message                │
│     │  · 注入 system prompt                                           │
│     ▼                                                                 │
│  providers/dashscope.py   DashScopeProvider.astream(lc_messages)      │
│     │  · LangChain ChatOpenAI(base_url=百炼, model=qwen-plus,         │
│     │    streaming=True)                                              │
│     ▼                                                                 │
│  protocol/ui_stream.py   UIStreamWriter  ──SSE──▶  浏览器             │
│     data: {"type":"text-delta","id":"...","delta":"你"}\n\n           │
└─────────────────────────────────────────────────────────────────────┘
```

### 一次请求的事件时序（SSE）

```
start → start-step → text-start → text-delta × N → text-end → finish-step → finish → [DONE]
```

> 出错时统一发 `error` 事件后终止。`text-start/delta/end` 共享同一个 `id`。

### 四个关键设计

| 设计点 | 文件 | 作用 |
|---|---|---|
| **协议层是唯一的「写线」入口** | `protocol/ui_stream.py` | Agent 绝不手拼字符串，所有 SSE 帧都经 `UIStreamWriter`；用 `asyncio.Queue` 解耦生产/消费。`tool-*` 方法已预留，待工具调用阶段启用。 |
| **Provider 抽象** | `providers/base.py` | `astream(messages) -> AsyncIterator[str]` 只暴露 token 文本增量。换 OpenAI / Anthropic / Ollama 只需新增一个文件。 |
| **Agent 抽象** | `agents/base.py` | `stream(messages, writer)`。路由只发外层 `start/finish`，不关心 Agent 内部策略；未来换 `ToolCallingAgent` / `ReActAgent`，路由一行不改。 |
| **前端 Transport 单一耦合点** | `web/src/services/chatTransport.ts` | UI 与后端契约的唯一耦合点。加鉴权头 / 换 WebSocket 只改这一个文件。 |

---

## 🧰 技术栈

| 层 | 技术 |
|---|---|
| **前端** | React 18 · TypeScript 5 · Vite 5 · Tailwind CSS 3 · Zustand 5 · `ai`@5 · `@ai-sdk/react`@2 · pnpm |
| **前端工程化** | ESLint 9 (flat config) · typescript-eslint 8 · Prettier 3 · Husky 9 · lint-staged 15 |
| **后端** | Python 3.11 · FastAPI · Uvicorn · Pydantic 2 · pydantic-settings · LangChain 0.3 · langchain-openai · uv · Ruff |
| **大模型** | 阿里云百炼（DashScope）OpenAI 兼容模式，默认 `qwen-plus` |
| **通信** | AI SDK v5 UI Message Stream Protocol（SSE / JSON 事件） |

---

## 📂 目录结构

```
basic-agent/
├── README.md                         # 本文件
├── docs/                             # 分阶段设计 & 交付文档
│   ├── stage-01-basic-chat.md        #   阶段01：基础聊天 + 可扩展架构
│   └── stage-02-frontend-tooling.md  #   阶段02：前端工程化
│
├── agent/                           # 后端服务（Python + FastAPI）
│   ├── pyproject.toml                # 依赖与构建（uv / hatchling）
│   ├── .env.example                  # 环境变量模板（复制为 .env）
│   └── src/basic_agent/
│       ├── main.py                   # FastAPI 入口、CORS、路由挂载
│       ├── core/
│       │   ├── config.py             # pydantic-settings 单例配置
│       │   └── logging.py
│       ├── schemas/
│       │   ├── ui_message.py         # UIMessage / UIPart（对齐 AI SDK v5）
│       │   └── chat.py               # ChatRequest
│       ├── protocol/
│       │   └── ui_stream.py          # ★ AI SDK v5 SSE writer（唯一写线）
│       ├── providers/
│       │   ├── base.py               # BaseLLMProvider 抽象
│       │   └── dashscope.py          # 百炼实现
│       ├── agents/
│       │   ├── base.py               # BaseAgent 抽象
│       │   └── chat_agent.py         # 当前纯聊天实现
│       ├── api/
│       │   ├── deps.py               # 依赖注入（provider/agent 单例）
│       │   └── routes/
│       │       ├── health.py         # GET  /api/health
│       │       └── chat.py           # POST /api/chat
│       ├── tools/                    # ★ 占位：未来工具
│       └── memory/                   # ★ 占位：未来会话/向量记忆
│
└── web/                             # 前端应用（React + Vite）
    ├── package.json
    ├── vite.config.ts                # /api → :8000 代理；@ → src 别名
    ├── .env.example
    └── src/
        ├── main.tsx, App.tsx
        ├── pages/ChatPage.tsx
        ├── components/chat/
        │   ├── ChatContainer.tsx     # useChat 装配
        │   ├── MessageList.tsx
        │   ├── MessageItem.tsx       # 渲染单条消息（遍历 parts）
        │   ├── MessageParts/
        │   │   ├── index.tsx         # ★ 按 part.type 分发渲染
        │   │   └── TextPart.tsx
        │   └── ChatInput.tsx         # Enter 发送 / Shift+Enter 换行
        ├── services/
        │   ├── chatTransport.ts      # ★ 后端契约的唯一耦合点
        │   └── http.ts               # 通用 JSON fetch
        ├── store/settingsStore.ts    # Zustand（systemPrompt 占位）
        ├── hooks/useAutoScroll.ts
        ├── types/chat.ts             # 重导出 ai 的 UIMessage
        └── lib/{env.ts, cn.ts}
```

---

## 🚀 快速开始

### 环境要求

| 工具 | 版本 | 说明 |
|---|---|---|
| Python | ≥ 3.11 | 后端 |
| [uv](https://docs.astral.sh/uv/) | 最新 | Python 包管理（`curl -LsSf https://astral.sh/uv/install.sh \| sh`） |
| Node.js | ≥ 18 | 前端（Vite 5 要求） |
| [pnpm](https://pnpm.io/) | ≥ 8 | 前端包管理（`npm i -g pnpm`） |
| 百炼 API Key | — | 阿里云 [DashScope](https://bailian.console.aliyun.com/) 控制台获取 |

### 1. 克隆

```bash
git clone https://github.com/AngeloWangCoder/basic-agent.git
cd basic-agent
```

### 2. 启动后端（终端 A）

```bash
cd agent
cp .env.example .env          # 然后编辑 .env，填入真实的 DASHSCOPE_API_KEY
uv sync                       # 创建虚拟环境并安装依赖
uv run uvicorn basic_agent.main:app --reload --port 8000
```

后端起在 `http://localhost:8000`，验证：`curl http://localhost:8000/api/health` → `{"ok":true}`

### 3. 启动前端（终端 B）

```bash
cd web
pnpm install                  # 安装依赖，并自动安置 Husky pre-commit hook
pnpm dev                      # http://localhost:5173
```

打开 `http://localhost:5173` 即可聊天。Vite 已把 `/api` 代理到 `:8000`，开发期无需处理 CORS。

> ⚠️ **前后端需同时运行**：前端聊天依赖后端 `:8000`。

---

## ⚙️ 配置

### 后端 `agent/.env`

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DASHSCOPE_API_KEY` | *(必填)* | 百炼 API Key |
| `DASHSCOPE_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | OpenAI 兼容端点 |
| `MODEL_NAME` | `qwen-plus` | 模型名（可换 `qwen-max` / `qwen-turbo` 等） |
| `TEMPERATURE` | `0.7` | 采样温度 |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | 监听地址 |
| `CORS_ORIGINS` | `http://localhost:5173` | 允许的前端源，**逗号分隔** |

### 前端 `web/.env`

| 变量 | 默认值 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | `/api` | 后端 API 前缀；生产部署可改为完整 URL |

---

## 🔌 API 参考

### `GET /api/health`

健康检查。返回 `{"ok": true}`。

### `POST /api/chat`

接收 AI SDK v5 `useChat` 提交的消息体，返回 **SSE 流**（`text/event-stream`）。

**请求体**

```jsonc
{
  "id": "会话/请求 id",
  "messages": [
    {
      "id": "u1",
      "role": "user",                  // system | user | assistant
      "parts": [{ "type": "text", "text": "你好" }]
    }
  ]
}
```

**响应头**（v5 客户端识别必需）

```
Content-Type: text/event-stream
x-vercel-ai-ui-message-stream: v1
```

**响应体**：每帧 `data: <json>\n\n`，以 `data: [DONE]\n\n` 结束。事件类型见上文「事件时序」。

**命令行冒烟测试**

```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"id":"t1","messages":[{"id":"u1","role":"user","parts":[{"type":"text","text":"用一句话介绍你自己"}]}]}'
```

预期看到 `text-delta` 事件逐段输出，最后 `finish` + `[DONE]`。

---

## 🧩 二次开发指南

项目的每个核心层都为扩展而设计。以下是最常见的几类扩展，均**不需要改动其他层**。

### 1. 接入一个新的大模型（Provider）

```python
# agent/src/basic_agent/providers/openai.py
from typing import AsyncIterator
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from .base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, settings):
        self._client = ChatOpenAI(model="gpt-4o", streaming=True)  # 读自己的 key

    async def astream(self, messages: list[BaseMessage]) -> AsyncIterator[str]:
        async for chunk in self._client.astream(messages):
            if isinstance(chunk.content, str) and chunk.content:
                yield chunk.content
```

然后在 `api/deps.py` 的 `get_provider()` 里返回它即可。路由、Agent、协议层都无需改动。

### 2. 换一种推理策略（Agent）

继承 `agents/base.py` 的 `BaseAgent`，实现 `stream(messages, writer)`：

```python
class ToolCallingAgent(BaseAgent):
    async def stream(self, messages, writer):
        # ... 调用带工具的模型，按需 writer.text_delta / writer.tool_input_start ...
```

在 `api/deps.py` 的 `get_chat_agent()` 里换成新 Agent。`api/routes/chat.py` 负责的 `start/finish` 生命周期事件保持不变。

### 3. 启用工具调用（Tool Calling）

协议层 `protocol/ui_stream.py` 已预留方法（当前未触发）：

```
tool_input_start / tool_input_delta / tool_input_available / tool_output_available
```

在新 Agent 里调用这些方法发出 `tool-*` 事件，前端再加对应渲染（见下条）即可打通工具调用 UI。`agent/tools/` 目录已为工具注册表预留。

### 4. 新增一种消息渲染类型（Message Part）

后端 `schemas/ui_message.py` 的 `UIPart` 是可辨识联合（discriminated union），且已有 `UIUnknownPart` 兜底，所以**新增 part 类型时后端通常无需改动**。前端只需两步：

```tsx
// web/src/components/chat/MessageParts/ToolPart.tsx   ← 新建
export function ToolPart(props) { /* 渲染工具调用 */ }

// web/src/components/chat/MessageParts/index.tsx       ← 加一个 case
switch (part.type) {
  case 'text': return <TextPart text={part.text} />;
  case 'tool-xxx': return <ToolPart ... />;   // ← 新增
  default: return null;
}
```

`MessageItem` / `MessageList` 一行不用改。

### 5. 定制前端与后端的通信（Transport）

只改 `web/src/services/chatTransport.ts` 一个文件，即可加鉴权头、拦截器或换协议：

```ts
export const chatTransport = new DefaultChatTransport({
  api: `${env.API_BASE_URL}/chat`,
  headers: { Authorization: `Bearer ${token}` },   // ← 例如加鉴权
});
```

### 扩展点速查表

| 想做的事 | 改这里 |
|---|---|
| 换 / 加大模型 | `agent/.../providers/` + `deps.py` |
| 换推理策略（ReAct/工具/多步） | `agent/.../agents/` + `deps.py` |
| 加协议事件 | `agent/.../protocol/ui_stream.py` |
| 加消息渲染类型 | `web/src/components/chat/MessageParts/` |
| 加鉴权 / 换传输 | `web/src/services/chatTransport.ts` |
| 持久化会话 / 记忆 | `agent/memory/`（占位） |
| 全局前端状态 | `web/src/store/settingsStore.ts` |

---

## 🛠️ 前端工程化

`web/` 内置 lint / format / git hook 工具链（详见 [`docs/stage-02-frontend-tooling.md`](./docs/stage-02-frontend-tooling.md)）。

| 命令 | 作用 |
|---|---|
| `pnpm dev` | 开发服务器（:5173） |
| `pnpm build` | 类型检查 + 生产构建 |
| `pnpm preview` | 预览生产构建 |
| `pnpm typecheck` | 仅 `tsc --noEmit` |
| `pnpm lint` / `pnpm lint:fix` | ESLint 校验 / 自动修复 |
| `pnpm format` / `pnpm format:check` | Prettier 写入 / 检查 |

提交时 Husky `pre-commit` 会对改动文件自动跑 `eslint --fix` + `prettier --write`（由 `pnpm install` 的 `prepare` 脚本自动安置，**要求项目根是 git 仓库**）。

---

## 📐 开发工作流（阶段制）

本项目按阶段推进，每个阶段先在 [`docs/`](./docs/) 写设计文档、审阅通过后再编码，最后把实际产出回填同一份文档作为交付物。

| 阶段 | 文档 | 内容 |
|---|---|---|
| 01 | [stage-01-basic-chat.md](./docs/stage-01-basic-chat.md) | 基础聊天 + 可扩展架构 |
| 02 | [stage-02-frontend-tooling.md](./docs/stage-02-frontend-tooling.md) | 前端工程化（ESLint + Prettier + Husky） |

---

## ⚠️ 已知踩坑（实施时已规避，二次开发请注意）

- **AI SDK v5 ≠ v4**：v4 是行前缀（`0:"..."`），v5 是 JSON 事件，二者不兼容。务必使用 `ai@^5` / `@ai-sdk/react@^2`。
- **必须发响应头 `x-vercel-ai-ui-message-stream: v1`**，否则 v5 `useChat` 拒绝解析（已固化在 `UI_MESSAGE_STREAM_HEADERS`）。
- **LangChain `ChatOpenAI` 接百炼**：显式 `streaming=True`，用 `.astream()` 而非 `.ainvoke()`。
- **`CORS_ORIGINS` 用 CSV 而非 JSON**：`config.py` 用 `NoDecode` + validator 解析逗号分隔字符串，不要写成 JSON 数组。
- **多轮对话的非文本 part**：v5 会回传 `step-start` / `tool-*` 等 part，后端 `UIUnknownPart` 已兜底接收，但只有 `text` part 进入 LLM 上下文。

---

## 📄 License

暂未指定。如需开源发布，建议在仓库根添加 `LICENSE`（如 MIT）。
