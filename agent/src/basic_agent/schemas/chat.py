from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .ui_message import UIMessage


class ChatRequest(BaseModel):
    """Request body posted by the AI SDK v5 useChat hook."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    messages: list[UIMessage]
    trigger: str | None = None
