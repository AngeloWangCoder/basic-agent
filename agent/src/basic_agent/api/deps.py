from __future__ import annotations

from functools import lru_cache

from ..agents.chat_agent import ChatAgent
from ..core.config import get_settings
from ..providers.base import BaseLLMProvider
from ..providers.dashscope import DashScopeProvider

_DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Reply in the user's language."


@lru_cache(maxsize=1)
def get_provider() -> BaseLLMProvider:
    return DashScopeProvider(get_settings())


@lru_cache(maxsize=1)
def get_chat_agent() -> ChatAgent:
    return ChatAgent(provider=get_provider(), system_prompt=_DEFAULT_SYSTEM_PROMPT)
