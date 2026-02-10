"""Chat API endpoints - WebSocket and HTTP for streaming chat with user isolation"""

import json
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.models.user import User
from src.models.conversation import MessageCreate, ChatResponse
from src.core.llm_client import get_llm_response
from src.core.streaming import StreamChunk
from src.core.auth import decode_access_token
from src.db.mongo import get_conversation_for_user, add_message_to_conversation
from src.agents import agent_registry
from src.services.attachment import attachment_service
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])
security = HTTPBearer()


class ConnectionManager:
    """WebSocket connection manager with user tracking"""

    def __init__(self):
        self.active_connections: dict[str, tuple[WebSocket, str]] = {}  # conv_id -> (websocket, user_id)

    async def connect(self, websocket: WebSocket, conv_id: str, user_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[conv_id] = (websocket, user_id)
        logger.info("WebSocket connected", conv_id=conv_id, user_id=user_id)

    def disconnect(self, conv_id: str):
        """Remove WebSocket connection"""
        if conv_id in self.active_connections:
            del self.active_connections[conv_id]
            logger.info("WebSocket disconnected", conv_id=conv_id)

    async def send_message(self, conv_id: str, message: str):
        """Send message to specific conversation"""
        if conv_id in self.active_connections:
            await self.active_connections[conv_id][0].send_text(message)


# Global connection manager
manager = ConnectionManager()


async def get_user_from_token(token: str) -> User:
    """Extract and validate user from JWT token"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    from src.db.mongo import get_user_by_id
    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return User(**user)


@router.post("/{conv_id}")
async def send_message(
    conv_id: str,
    message: MessageCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Send a message and get AI response (non-streaming).

    Args:
        conv_id: Conversation UUID
        message: Message to send
        credentials: JWT token

    Returns:
        ChatResponse with AI response

    Raises:
        HTTPException: If conversation not found or access denied
    """
    # Get user from token
    user = await get_user_from_token(credentials.credentials)

    logger.info("Sending message", conv_id=conv_id, user_id=user.id)

    # Get conversation with user ownership check
    conversation = await get_conversation_for_user(conv_id, user.id)
    if not conversation:
        logger.warning("Message failed: conversation not found or access denied", conv_id=conv_id, user_id=user.id)
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
    await add_message_to_conversation(
        conv_id=conv_id,
        user_id=user.id,
        role="user",
        content=message.content,
        attachments=message.attachments
    )

    updated_conversation = await add_message_to_conversation(
        conv_id=conv_id,
        user_id=user.id,
        role="assistant",
        content=response
    )

    # Get the message ID from the last message
    message_id = updated_conversation["messages"][-1]["id"] if updated_conversation["messages"] else str(uuid.uuid4())

    # Clean up attachments
    if message.attachments:
        await attachment_service.cleanup_files(message.attachments)

    logger.info("Message sent successfully", conv_id=conv_id, user_id=user.id)

    return ChatResponse(
        message_id=message_id,
        content=response,
        done=True
    )


@router.websocket("/ws/{conv_id}")
async def websocket_chat(websocket: WebSocket, conv_id: str, token: str = Query(...)):
    """
    WebSocket endpoint for streaming chat.

    Query Parameters:
        token: JWT authentication token

    Args:
        websocket: WebSocket connection
        conv_id: Conversation UUID
    """

    # Authenticate user from token
    try:
        user = await get_user_from_token(token)
    except Exception as e:
        await websocket.accept()
        await websocket.send_text(json.dumps({
            "content": "",
            "done": True,
            "metadata": {},
            "error": "Authentication failed"
        }))
        await websocket.close()
        return

    # Verify user has access to this conversation
    conversation = await get_conversation_for_user(conv_id, user.id)
    if not conversation:
        await websocket.accept()
        await websocket.send_text(json.dumps({
            "content": "",
            "done": True,
            "metadata": {},
            "error": "Conversation not found"
        }))
        await websocket.close()
        return

    await manager.connect(websocket, conv_id, user.id)

    logger.info("WebSocket chat started", conv_id=conv_id, user_id=user.id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            content = message_data.get("content", "")
            attachments = message_data.get("attachments", [])

            logger.info("WebSocket message received", conv_id=conv_id, user_id=user.id)

            # Build message history
            messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation.get("messages", [])
            ]
            messages.append({"role": "user", "content": content})

            # Save user message
            await add_message_to_conversation(
                conv_id=conv_id,
                user_id=user.id,
                role="user",
                content=content,
                attachments=attachments
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
                await add_message_to_conversation(
                    conv_id=conv_id,
                    user_id=user.id,
                    role="assistant",
                    content=full_response
                )

                # Update conversation reference
                conversation = await get_conversation_for_user(conv_id, user.id)

                # Clean up attachments
                if attachments:
                    await attachment_service.cleanup_files(attachments)

                logger.info("WebSocket response sent", conv_id=conv_id, user_id=user.id)

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
        logger.info("WebSocket disconnected normally", conv_id=conv_id, user_id=user.id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        manager.disconnect(conv_id)
