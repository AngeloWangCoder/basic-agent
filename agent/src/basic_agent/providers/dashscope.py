from __future__ import annotations

from typing import AsyncIterator

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from ..core.config import Settings
from .base import BaseLLMProvider


class DashScopeProvider(BaseLLMProvider):
    """LangChain ChatOpenAI configured for Aliyun DashScope's OpenAI-compatible endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._client = ChatOpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            model=settings.model_name,
            temperature=settings.temperature,
            streaming=True,
        )

    async def astream(self, messages: list[BaseMessage]) -> AsyncIterator[str]:
        async for chunk in self._client.astream(messages):
            content = chunk.content
            if not content:
                continue
            if isinstance(content, str):
                yield content
            else:
                # Defensive: LangChain may emit list[dict] content for multimodal.
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text = part.get("text", "")
                        if text:
                            yield text
