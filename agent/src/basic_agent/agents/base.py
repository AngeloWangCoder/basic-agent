from __future__ import annotations

from abc import ABC, abstractmethod

from ..protocol.ui_stream import UIStreamWriter
from ..schemas.ui_message import UIMessage


class BaseAgent(ABC):
    """Contract every agent must implement.

    Agents consume the request's UIMessage list and emit protocol events
    through the shared ``UIStreamWriter``. Returning means the agent finished
    producing content for this turn; the route handler is responsible for
    sending the surrounding ``start`` / ``finish`` lifecycle events.
    """

    @abstractmethod
    async def stream(
        self,
        messages: list[UIMessage],
        writer: UIStreamWriter,
    ) -> None:
        raise NotImplementedError
