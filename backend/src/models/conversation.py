"""Pydantic models for conversations and messages"""

from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message model"""

    id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    role: Literal["user", "assistant", "system"] = Field(description="Message role")
    content: str = Field(default="", description="Message content (text or markdown)")
    attachments: List[str] = Field(default_factory=list, description="List of attachment file IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    """Conversation model"""

    id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    title: str = Field(default="New Conversation", description="Conversation title")
    messages: List[Message] = Field(default_factory=list, description="Message history")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationCreate(BaseModel):
    """Request model for creating a conversation"""

    title: Optional[str] = Field(default="New Conversation", description="Initial title")


class ConversationUpdate(BaseModel):
    """Request model for updating a conversation"""

    title: Optional[str] = Field(default=None, description="New title")


class MessageCreate(BaseModel):
    """Request model for creating a message"""

    content: str = Field(..., description="Message content")
    attachments: List[str] = Field(default_factory=list, description="Attachment file IDs")
    stream: bool = Field(default=True, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Response model for chat messages"""

    message_id: str = Field(..., description="Message ID")
    content: str = Field(default="", description="Response content")
    done: bool = Field(default=False, description="Whether the stream is complete")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FileUpload(BaseModel):
    """Response model for file upload"""

    file_id: str = Field(..., description="Unique file ID")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="File MIME type")
    size: int = Field(..., description="File size in bytes")
    temp_path: str = Field(..., description="Temporary file path")


class AgentInfo(BaseModel):
    """Agent information model"""

    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    category: str = Field(default="general", description="Agent category")


class IntentResult(BaseModel):
    """Intent recognition result"""

    intent: str = Field(..., description="Recognized intent")
    confidence: float = Field(default=0.0, description="Confidence score")
    agent: Optional[str] = Field(default=None, description="Target agent name")
    reasoning: str = Field(default="", description="Intent reasoning")
