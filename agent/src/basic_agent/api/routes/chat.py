from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ...agents.base import BaseAgent
from ...protocol.ui_stream import UI_MESSAGE_STREAM_HEADERS, UIStreamWriter
from ...schemas.chat import ChatRequest
from ..deps import get_chat_agent

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat")
async def chat(
    body: ChatRequest,
    agent: BaseAgent = Depends(get_chat_agent),
) -> StreamingResponse:
    writer = UIStreamWriter()

    async def run() -> None:
        try:
            await writer.start()
            await writer.start_step()
            await agent.stream(body.messages, writer)
            await writer.finish_step()
            await writer.finish()
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent stream failed")
            await writer.error(str(exc))
        finally:
            await writer.close()

    asyncio.create_task(run())

    return StreamingResponse(
        writer.iterator(),
        media_type="text/event-stream",
        headers=UI_MESSAGE_STREAM_HEADERS,
    )
