# Stage 01 · 基础聊天 + 可扩展架构（已交付）

| 项目 | 内容 |
|---|---|
| 日期 | 2026-05-23 |
| 范围 | 跑通「用户输入 → 流式回复」最小闭环 |
| 状态 | 代码已交付；本地依赖安装与端到端冒烟测试由用户在 shell 执行 |

---

## 1. 背景与目标

`basic-agent/` 下原本只有两个空目录 `web/` 与 `agent/`，需要从 0 起一个类 Claude Code 的智能体项目。第一阶段只做最朴素的「问 → 答」聊天，但代码骨架必须为后续工具调用、文件操作、多轮记忆、ReAct/PlanExecute 等能力打好抽象，避免推翻重来。

**不做**：工具调用、多会话持久化、文件附件、模型选择 UI、鉴权、日志/监控、错误重试策略。这些都在后续阶段。

---

## 2. 技术决策

| 项 | 选择 | 理由 |
|---|---|---|
| 前端栈 | pnpm + Vite + React 18 + TypeScript + Zustand + Tailwind | 用户既定 |
| 聊天 UI | `@ai-sdk/react`（v2.x）+ `ai`（v5.x）`useChat` | 用户既定 |
| 后端栈 | Python 3.11 + FastAPI + LangChain | FastAPI 异步原生 + LangChain 流式输出最熟，未来加工具调用最顺 |
| Python 包管理 | `uv` | 速度快、原生 `pyproject.toml`、2026 年事实标准 |
| LLM | 阿里云百炼 OpenAI 兼容模式，模型 `qwen-plus` | 用户既定 base_url；qwen-plus 综合质量与速度均衡 |
| 通信协议 | **AI SDK v5 UI Message Stream Protocol**（SSE / JSON 事件） | 与 useChat 零配置对接；未来工具调用/文件附件可直接复用 part 渲染 |
| API key | `agent/.env`（gitignore）+ `agent/.env.example`（占位） | 不入仓 |
| 开发期跨域 | Vite proxy `/api → http://localhost:8000` | 避免 CORS；CORS 中间件保留 |

---

## 3. 目录结构（实际产出）

### `agent/`

```
agent/
├── .env / .env.example / .gitignore / .python-version
├── pyproject.toml
├── README.md
└── src/basic_agent/
    ├── main.py                       # FastAPI 入口、CORS、路由挂载
    ├── core/
    │   ├── config.py                 # pydantic-settings，单例 settings
    │   └── logging.py
    ├── schemas/
    │   ├── ui_message.py             # UIMessage（与 AI SDK 对齐）
    │   └── chat.py                   # ChatRequest
    ├── protocol/
    │   └── ui_stream.py              # ★ AI SDK v5 SSE writer
    ├── providers/
    │   ├── base.py                   # BaseLLMProvider 抽象
    │   └── dashscope.py              # LangChain ChatOpenAI → 百炼
    ├── agents/
    │   ├── base.py                   # BaseAgent 抽象（stream(messages, writer)）
    │   └── chat_agent.py             # 当前实现
    ├── api/
    │   ├── deps.py                   # provider/agent 依赖注入（lru_cache 单例）
    │   └── routes/
    │       ├── health.py             # GET /api/health
    │       └── chat.py               # POST /api/chat → StreamingResponse
    ├── tools/README.md               # ★ 占位：未来工具
    └── memory/README.md              # ★ 占位：未来记忆/历史
```

### `web/`

```
web/
├── package.json, tsconfig*.json
├── vite.config.ts                    # /api → :8000 proxy；@ → src 别名
├── tailwind.config.js, postcss.config.js, index.html
├── .env.example, .gitignore, README.md
└── src/
    ├── main.tsx, App.tsx, index.css, vite-env.d.ts
    ├── pages/ChatPage.tsx
    ├── components/chat/
    │   ├── ChatContainer.tsx         # useChat 装配
    │   ├── MessageList.tsx           # 滚动 + 状态占位
    │   ├── MessageItem.tsx           # 渲染单条 UIMessage（map parts）
    │   ├── MessageParts/
    │   │   ├── index.tsx             # ★ 按 part.type 分发
    │   │   └── TextPart.tsx
    │   └── ChatInput.tsx             # Enter 发送 / Shift+Enter 换行 / 停止
    ├── store/settingsStore.ts        # zustand（systemPrompt 占位）
    ├── services/
    │   ├── chatTransport.ts          # ★ DefaultChatTransport，集中配置
    │   └── http.ts                   # 通用 JSON fetch
    ├── hooks/useAutoScroll.ts
    ├── types/chat.ts                 # 重导出 ai 的 UIMessage
    └── lib/{env.ts, cn.ts}
```

---

## 4. 关键模块设计

### 4.1 协议层（最关键，独立成模块）

`agent/src/basic_agent/protocol/ui_stream.py` 是输出 AI SDK v5 UI Message Stream Protocol 字节流的唯一入口；Agent 不直接拼字符串。

**响应头**（必须）
```
Content-Type: text/event-stream
Cache-Control: no-cache, no-transform
Connection: keep-alive
x-vercel-ai-ui-message-stream: v1     ← v5 客户端识别必需
```

**事件帧**：`data: <json>\n\n`，结束追加 `data: [DONE]\n\n`

**本阶段事件**
- `start` / `start-step` / `text-start` / `text-delta` / `text-end` / `finish-step` / `finish` / `error`
- 同一文本块 `text-start/delta/end` 的 `id` 必须一致

**为未来预留的方法**（已实现签名，不会触发，等工具调用阶段启用）
- `tool_input_start / tool_input_delta / tool_input_available / tool_output_available`

实现细节：`asyncio.Queue` 生产-消费模式，路由侧 `StreamingResponse(writer.iterator(), media_type="text/event-stream", headers=UI_MESSAGE_STREAM_HEADERS)`，agent 通过 `asyncio.create_task` 并发把事件喂进队列，错误统一翻译成 `error` 事件 + 终止。

### 4.2 Provider 抽象

`BaseLLMProvider.astream(messages) -> AsyncIterator[str]`：只暴露 token-level 文本增量。`DashScopeProvider` 用 `langchain_openai.ChatOpenAI(base_url=..., api_key=..., model="qwen-plus", streaming=True)` 包一层；防御性地处理 `chunk.content` 可能是 list[dict]（多模态）的情况。未来加 OpenAI / Anthropic / Ollama 只新增文件。

### 4.3 Agent 抽象

`BaseAgent.stream(messages: list[UIMessage], writer: UIStreamWriter) -> None`。当前实现 `ChatAgent`：
1. UIMessage → LangChain `HumanMessage` / `AIMessage` / `SystemMessage`（仅取 text part）
2. 注入可选 `system_prompt`（仅当历史里没有 system 时）
3. `provider.astream(...)` → `writer.text_delta(...)`，统一 `text_id`

路由层只发外层 `start/finish`，不关心 agent 内部用什么协议事件，未来换 `ToolCallingAgent` / `ReActAgent` 路由不动。

### 4.4 Schemas 与 useChat v5 对齐

```python
class UITextPart(BaseModel):
    type: Literal["text"]
    text: str

UIPart = Annotated[Union[UITextPart], Field(discriminator="type")]

class UIMessage(BaseModel):
    id: str
    role: Literal["system","user","assistant"]
    parts: list[UIPart]

class ChatRequest(BaseModel):
    id: str | None = None
    messages: list[UIMessage]
    trigger: str | None = None
    model_config = ConfigDict(extra="ignore")   # 容忍 v5 额外字段
```

`UIPart` 当前只有 `UITextPart`，但写成 `Annotated[Union[...], Field(discriminator="type")]`，未来扩展只在 union 里加新成员。

### 4.5 前端 Transport 服务层

`web/src/services/chatTransport.ts` 是聊天 UI 与后端契约的唯一耦合点。`ChatContainer` 用 `useChat({ transport: chatTransport })`，未来切自定义 transport（auth header / WebSocket / 拦截器）只改这一个文件。

### 4.6 前端 Parts 分发

`MessageParts/index.tsx`：
```tsx
switch (part.type) {
  case 'text': return <TextPart text={part.text} />;
  default:     return null;
}
```
新增 part 类型（如 tool / file / image）只在 `MessageParts/` 加文件 + 加 case，`MessageItem` 与 `MessageList` 一行不改。

---

## 5. 扩展点对照表

| 模块 | 当前形态 | 未来用途 |
|---|---|---|
| `providers/base.py` | 只 `astream` | 多供应商 / 多模态 / 函数调用 |
| `agents/base.py` | `ChatAgent` | `ToolCallingAgent` / `ReActAgent` / `PlanExecuteAgent` |
| `protocol/ui_stream.py` | text/finish/error 已用，tool-* 已留方法 | 工具调用、data part、step 多步 |
| `tools/` `memory/` | README 占位 | 工具注册表、会话/向量记忆 |
| 前端 `MessageParts/` | 仅 TextPart | ToolPart / FilePart / ImagePart |
| 前端 `services/chatTransport.ts` | DefaultChatTransport | 自定义 transport / 鉴权 |
| 前端 `store/` | settings | sessions / artifacts / tool runs |

---

## 6. 实施步骤（已执行）

1. ✅ 写 `agent/pyproject.toml`、`.env*`、`.gitignore`、`.python-version`、`README.md`
2. ✅ 写 `core/`、`schemas/`、`protocol/ui_stream.py`
3. ✅ 写 `providers/`、`agents/`、`api/deps.py`
4. ✅ 写 `api/routes/health.py` + `chat.py`、`main.py`
5. ✅ 写 `web/package.json`、`tsconfig*`、`vite.config.ts`、Tailwind/PostCSS 配置、`index.html`、`.env.example/.gitignore/README.md`
6. ✅ 写 `web/src/**`：UI 组件、store、services、hooks、lib
7. ⏸️ 依赖安装与本地启动 —— 由用户在 shell 执行（见 §7）

---

## 7. 验证方式（请按顺序执行）

```bash
# 后端 ─ terminal A
cd /Users/angelo/Desktop/AI/basic-agent/agent
uv sync
uv run uvicorn basic_agent.main:app --reload --port 8000

# 前端 ─ terminal B
cd /Users/angelo/Desktop/AI/basic-agent/web
pnpm install
pnpm dev          # http://localhost:5173
```

验证清单
1. `curl http://localhost:8000/api/health` → `{"ok":true}`
2. ```bash
   curl -N -X POST http://localhost:8000/api/chat \
     -H 'Content-Type: application/json' \
     -d '{"id":"t1","messages":[{"id":"u1","role":"user","parts":[{"type":"text","text":"用一句话介绍你自己"}]}]}'
   ```
   预期：响应头含 `x-vercel-ai-ui-message-stream: v1`；流式输出 `start` → `start-step` → `text-start` → 多次 `text-delta` → `text-end` → `finish-step` → `finish` → `[DONE]`。
3. 浏览器打开 `http://localhost:5173`，输入消息：
   - 气泡逐字流式显现
   - DevTools → Network → `/api/chat` 类型为 SSE，事件为 JSON
4. 故意把 `.env` 的 `DASHSCOPE_API_KEY` 改错重启 → 前端显示错误状态

---

## 8. 已知踩坑提示（实施时已规避）

- **AI SDK v5 与 v4 协议不兼容**：v4 行前缀（`0:"..."`），v5 是 JSON 事件。务必装 `ai@^5` / `@ai-sdk/react@^2`
- **必须发响应头 `x-vercel-ai-ui-message-stream: v1`**，否则 v5 useChat 拒绝解析（已在 `UI_MESSAGE_STREAM_HEADERS` 常量中固化）
- **LangChain `ChatOpenAI` 对接百炼**：显式 `streaming=True`，用 `.astream()` 而非 `.ainvoke()`
- **pydantic-settings 的 `.env`** 相对启动目录解析；`core/config.py` 用绝对路径 `_AGENT_ROOT / ".env"` 锁死
- **`.env` 已加进 `.gitignore`**；提交仓库时只有 `.env.example`

---

## 8.1 实施后修复（Errata）

### E1 · `cors_origins` JSON 解析失败导致后端无法启动

**症状**：`uvicorn` 启动报 `pydantic_settings.exceptions.SettingsError: error parsing value for field "cors_origins"`，链中包含 `json.decoder.JSONDecodeError`。

**根因**：pydantic-settings v2 对 `list[str]` 这类复杂字段，会先尝试 `json.loads(env_value)` 再走 `field_validator`。CSV 字符串 `http://localhost:5173` 直接抛 JSON 错，validator 跑不到。

**修复**：把字段改为 `Annotated[list[str], NoDecode]`，跳过自动 JSON 解析。`.env` 写法保持 CSV 不变。

### E2 · 第二轮对话报 `union_tag_invalid` (`step-start`)

**症状**：第一轮 OK；第二轮请求时报 `Input tag 'step-start' found using 'type' does not match any of the expected tags: 'text'`。

**根因**：AI SDK v5 useChat 在历史 assistant 消息的 `parts` 中携带 `step-start`（以及未来的 `tool-*` / `reasoning` / `source-*` 等元数据 part）回传到后端；原 `UIPart` 是 `Annotated[Union[UITextPart], discriminator="type"]`，只认 `text`。

**修复**：`UIPart = Union[UITextPart, UIUnknownPart]`（去 discriminator），`UIUnknownPart` 用 `type: str` + `extra="allow"` 接住所有未知 type。`UIMessage.text` 只挑 `UITextPart` 拼，非文本 part 不进 LLM 上下文。Pydantic v2 smart union 顺序匹配先严格后宽松，安全。

---

## 9. 交付清单

后端 25 个文件 / 前端 26 个文件 / 根 3 个文件，共 54 个新文件。完整清单见仓库 `find /Users/angelo/Desktop/AI/basic-agent -type f -not -path '*/node_modules/*' -not -path '*/.venv/*'`。

关键文件实施时重点关注：
- `agent/src/basic_agent/protocol/ui_stream.py`
- `agent/src/basic_agent/api/routes/chat.py`
- `agent/src/basic_agent/agents/chat_agent.py`
- `agent/src/basic_agent/providers/dashscope.py`
- `web/src/services/chatTransport.ts`
- `web/src/components/chat/ChatContainer.tsx`
- `web/src/components/chat/MessageParts/index.tsx`
