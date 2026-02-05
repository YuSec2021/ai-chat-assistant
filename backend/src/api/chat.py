"""Chat API endpoints - WebSocket and HTTP for streaming chat"""

import json
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from bson import ObjectId
from src.db.mongo import get_database
from src.models.conversation import MessageCreate, ChatResponse
from src.core.llm_client import get_llm_response
from src.core.streaming import StreamChunk, stream_llm_response
from src.agents import agent_registry
from src.services.attachment import attachment_service
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ConnectionManager:
    """WebSocket connection manager"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, conv_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[conv_id] = websocket
        logger.info("WebSocket connected", conv_id=conv_id)

    def disconnect(self, conv_id: str):
        """Remove WebSocket connection"""
        if conv_id in self.active_connections:
            del self.active_connections[conv_id]
            logger.info("WebSocket disconnected", conv_id=conv_id)

    async def send_message(self, conv_id: str, message: str):
        """Send message to specific conversation"""
        if conv_id in self.active_connections:
            await self.active_connections[conv_id].send_text(message)


# Global connection manager
manager = ConnectionManager()


@router.post("/{conv_id}")
async def send_message(conv_id: str, message: MessageCreate):
    """Send a message and get AI response (non-streaming)"""

    db = await get_database()

    # Get conversation
    try:
        conversation = await db.conversations.find_one({"_id": ObjectId(conv_id)})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception:
        # Try with string ID
        conversation = await db.conversations.find_one({"id": conv_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Build message history
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in conversation.get("messages", [])
    ]
    messages.append({"role": "user", "content": message.content})

    # Get response from supervisor agent
    supervisor = agent_registry.get("Supervisor")

    try:
        response = await supervisor.execute(
            message.content,
            context={"messages": messages, "attachments": message.attachments}
        )
    except Exception as e:
        logger.error("Chat response failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    # Save messages to database
    user_message = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": message.content,
        "attachments": message.attachments,
        "timestamp": datetime.utcnow().isoformat()
    }

    assistant_message = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": response,
        "timestamp": datetime.utcnow().isoformat()
    }

    await db.conversations.update_one(
        {"_id": ObjectId(conv_id)},
        {
            "$push": {"messages": {"$each": [user_message, assistant_message]}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    # Clean up attachments
    if message.attachments:
        await attachment_service.cleanup_files(message.attachments)

    return ChatResponse(
        message_id=assistant_message["id"],
        content=response,
        done=True
    )


@router.websocket("/ws/{conv_id}")
async def websocket_chat(websocket: WebSocket, conv_id: str):
    """WebSocket endpoint for streaming chat"""

    await manager.connect(websocket, conv_id)
    db = await get_database()

    try:
        # Get conversation
        conversation = await db.conversations.find_one({"id": conv_id})
        if not conversation:
            await websocket.send_text(json.dumps({"error": "Conversation not found"}))
            await websocket.close()
            return

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            content = message_data.get("content", "")
            attachments = message_data.get("attachments", [])

            # Build message history
            messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation.get("messages", [])
            ]
            messages.append({"role": "user", "content": content})

            # Save user message
            user_message = {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": content,
                "attachments": attachments,
                "timestamp": datetime.utcnow().isoformat()
            }

            await db.conversations.update_one(
                {"id": conv_id},
                {"$push": {"messages": user_message}}
            )

            # Get streaming response from LLM
            from src.core.llm_client import get_llm_response_stream

            # Build full response
            full_response = ""
            message_id = str(uuid.uuid4())

            try:
                # Get streaming response
                async for chunk in get_llm_response_stream(messages):
                    # Send each chunk
                    stream_chunk = StreamChunk(
                        content=chunk,
                        done=False,
                        metadata={"message_id": message_id}
                    )
                    await websocket.send_text(stream_chunk.to_json())
                    full_response += chunk

                # Send final chunk
                final_chunk = StreamChunk(
                    content="",
                    done=True,
                    metadata={"message_id": message_id}
                )
                await websocket.send_text(final_chunk.to_json())

                # Save assistant message
                assistant_message = {
                    "id": message_id,
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.utcnow().isoformat()
                }

                await db.conversations.update_one(
                    {"id": conv_id},
                    {
                        "$push": {"messages": assistant_message},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )

                # Clean up attachments
                if attachments:
                    await attachment_service.cleanup_files(attachments)

            except Exception as e:
                logger.error("Chat streaming failed", error=str(e))
                error_chunk = StreamChunk(
                    content="",
                    done=True,
                    metadata={"message_id": message_id},
                    error=str(e)
                )
                await websocket.send_text(error_chunk.to_json())

    except WebSocketDisconnect:
        manager.disconnect(conv_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        manager.disconnect(conv_id)
