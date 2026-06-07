from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from langchain_core.messages import BaseMessage


class BaseLLMProvider(ABC):
    """Minimal LLM provider contract.

    Only token-level text streaming is required at this stage; tool/function
    calling is intentionally absent so the interface stays small. Subclasses
    can add capabilities (e.g. ``ainvoke_with_tools``) as the agent layer
    grows.
    """

    @abstractmethod
    def astream(self, messages: list[BaseMessage]) -> AsyncIterator[str]:
        """Yield incremental text chunks for the given LangChain messages."""
        raise NotImplementedError
