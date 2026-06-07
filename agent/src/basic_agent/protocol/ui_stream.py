"""
AI SDK v5 UI Message Stream Protocol writer.

Each event is emitted as a single SSE frame:

    data: <json>\\n\\n

The stream is terminated with the literal sentinel:

    data: [DONE]\\n\\n

The response must include the header
``x-vercel-ai-ui-message-stream: v1`` for the v5 client to consume it.

This module is the single source of truth for the wire format; agents must
go through ``UIStreamWriter`` rather than crafting frames by hand.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator


# Header required by AI SDK v5 useChat to recognise this stream protocol.
UI_MESSAGE_STREAM_HEADERS: dict[str, str] = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "x-vercel-ai-ui-message-stream": "v1",
}

_DONE = "data: [DONE]\n\n"


class UIStreamWriter:
    """Producer-side writer backed by an asyncio queue.

    The route handler hands the iterator to ``StreamingResponse`` while the
    agent concurrently calls the typed ``text_*`` / ``tool_*`` helpers.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._closed = False

    @staticmethod
    def _frame(event: dict[str, Any]) -> str:
        return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    async def _put(self, frame: str) -> None:
        if self._closed:
            return
        await self._queue.put(frame)

    async def write(self, event: dict[str, Any]) -> None:
        await self._put(self._frame(event))

    async def close(self) -> None:
        """Emit the terminator and stop the iterator."""
        if self._closed:
            return
        self._closed = True
        await self._queue.put(_DONE)
        await self._queue.put(None)

    async def iterator(self) -> AsyncIterator[str]:
        while True:
            item = await self._queue.get()
            if item is None:
                return
            yield item

    # ---- text events ------------------------------------------------------

    async def start(self) -> None:
        await self.write({"type": "start"})

    async def start_step(self) -> None:
        await self.write({"type": "start-step"})

    async def text_start(self, text_id: str) -> None:
        await self.write({"type": "text-start", "id": text_id})

    async def text_delta(self, text_id: str, delta: str) -> None:
        await self.write({"type": "text-delta", "id": text_id, "delta": delta})

    async def text_end(self, text_id: str) -> None:
        await self.write({"type": "text-end", "id": text_id})

    async def finish_step(self) -> None:
        await self.write({"type": "finish-step"})

    async def finish(self) -> None:
        await self.write({"type": "finish"})

    async def error(self, message: str) -> None:
        await self.write({"type": "error", "errorText": message})

    # ---- tool events (reserved for future use) ----------------------------

    async def tool_input_start(self, tool_call_id: str, tool_name: str) -> None:
        await self.write(
            {
                "type": "tool-input-start",
                "toolCallId": tool_call_id,
                "toolName": tool_name,
            }
        )

    async def tool_input_delta(self, tool_call_id: str, delta: str) -> None:
        await self.write(
            {
                "type": "tool-input-delta",
                "toolCallId": tool_call_id,
                "inputTextDelta": delta,
            }
        )

    async def tool_input_available(
        self, tool_call_id: str, tool_name: str, input_obj: dict[str, Any]
    ) -> None:
        await self.write(
            {
                "type": "tool-input-available",
                "toolCallId": tool_call_id,
                "toolName": tool_name,
                "input": input_obj,
            }
        )

    async def tool_output_available(
        self, tool_call_id: str, output: Any
    ) -> None:
        await self.write(
            {
                "type": "tool-output-available",
                "toolCallId": tool_call_id,
                "output": output,
            }
        )
