from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict


class UITextPart(BaseModel):
    """A plain-text part inside a UIMessage (AI SDK v5)."""

    type: Literal["text"]
    text: str


class UIUnknownPart(BaseModel):
    """Catch-all for non-text parts emitted by AI SDK v5 useChat.

    The client round-trips parts like ``step-start``, ``tool-*``, ``reasoning``,
    ``source-*`` etc. as part of the conversation history. We accept them so
    multi-turn chat works, but only ``UITextPart`` reaches the LLM context.
    """

    model_config = ConfigDict(extra="allow")

    type: str


# Smart-union order matters: pydantic v2 will try the stricter Literal first;
# anything else falls through to the catch-all.
UIPart = Union[UITextPart, UIUnknownPart]


class UIMessage(BaseModel):
    """A single message in the AI SDK v5 UI message shape."""

    model_config = ConfigDict(extra="ignore")

    id: str
    role: Literal["system", "user", "assistant"]
    parts: list[UIPart]

    @property
    def text(self) -> str:
        """Concatenated text from all text parts (other parts are ignored)."""
        return "".join(p.text for p in self.parts if isinstance(p, UITextPart))
