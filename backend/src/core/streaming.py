"""Streaming utilities for WebSocket and SSE"""

import json
import asyncio
from typing import AsyncIterator, Any, Dict
import structlog

logger = structlog.get_logger(__name__)


class StreamChunk:
    """Streaming response chunk"""

    def __init__(
        self,
        content: str = "",
        done: bool = False,
        metadata: Dict[str, Any] = None,
        error: str = None
    ):
        self.content = content
        self.done = done
        self.metadata = metadata or {}
        self.error = error

    def to_json(self) -> str:
        """Convert chunk to JSON"""
        data = {
            "content": self.content,
            "done": self.done,
            "metadata": self.metadata,
        }
        if self.error:
            data["error"] = self.error
        return json.dumps(data)


async def stream_llm_response(
    llm_iterator: AsyncIterator[str],
    message_id: str
) -> AsyncIterator[StreamChunk]:
    """Stream LLM response as chunks"""
    try:
        async for chunk in llm_iterator:
            yield StreamChunk(content=chunk, done=False, metadata={"message_id": message_id})

        # Send final chunk
        yield StreamChunk(content="", done=True, metadata={"message_id": message_id})

    except Exception as e:
        logger.error("Error streaming LLM response", error=str(e))
        yield StreamChunk(
            content="",
            done=True,
            metadata={"message_id": message_id},
            error=str(e)
        )


async def merge_streams(*streams: AsyncIterator[Any]) -> AsyncIterator[Any]:
    """Merge multiple async iterators into one"""
    queue = asyncio.Queue()

    async def producer(stream: AsyncIterator[Any]):
        async for item in stream:
            await queue.put(item)

    # Start all producers
    tasks = [asyncio.create_task(producer(stream)) for stream in streams]

    # Yield items from queue
    try:
        while any(not t.done() for t in tasks):
            try:
                item = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield item
            except asyncio.TimeoutError:
                continue
    finally:
        for task in tasks:
            task.cancel()
