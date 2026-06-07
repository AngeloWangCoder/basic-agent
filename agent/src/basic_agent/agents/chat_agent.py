from __future__ import annotations

import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from ..protocol.ui_stream import UIStreamWriter
from ..providers.base import BaseLLMProvider
from ..schemas.ui_message import UIMessage
from .base import BaseAgent


def _to_langchain_messages(messages: list[UIMessage]) -> list[BaseMessage]:
    lc: list[BaseMessage] = []
    for m in messages:
        content = m.text
        if not content:
            continue
        if m.role == "user":
            lc.append(HumanMessage(content=content))
        elif m.role == "assistant":
            lc.append(AIMessage(content=content))
        elif m.role == "system":
            lc.append(SystemMessage(content=content))
    return lc


class ChatAgent(BaseAgent):
    """A plain chat agent: stream model text through the writer, no tools."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        system_prompt: str | None = None,
    ) -> None:
        self._provider = provider
        self._system_prompt = system_prompt

    async def stream(
        self,
        messages: list[UIMessage],
        writer: UIStreamWriter,
    ) -> None:
        lc_messages = _to_langchain_messages(messages)
        if self._system_prompt and not any(isinstance(m, SystemMessage) for m in lc_messages):
            lc_messages.insert(0, SystemMessage(content=self._system_prompt))

        text_id = uuid.uuid4().hex
        await writer.text_start(text_id)
        try:
            async for delta in self._provider.astream(lc_messages):
                if delta:
                    await writer.text_delta(text_id, delta)
        finally:
            await writer.text_end(text_id)
