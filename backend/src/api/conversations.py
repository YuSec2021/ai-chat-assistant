"""Conversations API endpoints"""

import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from src.db.mongo import get_database
from src.models.conversation import Conversation, ConversationCreate, ConversationUpdate
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=List[Conversation])
async def list_conversations():
    """List all conversations"""

    db = await get_database()

    cursor = db.conversations.find().sort("updated_at", -1)
    conversations = await cursor.to_list(length=100)

    # Remove _id field (we use 'id' field instead)
    for conv in conversations:
        if "_id" in conv:
            del conv["_id"]

    return conversations


@router.post("", response_model=Conversation)
async def create_conversation(data: ConversationCreate):
    """Create a new conversation"""

    db = await get_database()

    conversation_id = str(uuid.uuid4())
    conversation = {
        "id": conversation_id,
        "title": data.title,
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {}
    }

    await db.conversations.insert_one(conversation)

    logger.info("Conversation created", conv_id=conversation_id)

    return Conversation(**conversation)


@router.get("/{conv_id}", response_model=Conversation)
async def get_conversation(conv_id: str):
    """Get a specific conversation"""

    db = await get_database()

    # First try to find by 'id' field (UUID), then by '_id' (ObjectId)
    conversation = await db.conversations.find_one({"id": conv_id})
    if not conversation:
        try:
            conversation = await db.conversations.find_one({"_id": ObjectId(conv_id)})
        except Exception:
            pass

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Remove _id field
    if "_id" in conversation:
        del conversation["_id"]

    return Conversation(**conversation)


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    """Delete a conversation"""

    db = await get_database()

    try:
        result = await db.conversations.delete_one({"_id": ObjectId(conv_id)})
    except Exception:
        result = await db.conversations.delete_one({"id": conv_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    logger.info("Conversation deleted", conv_id=conv_id)

    return {"message": "Conversation deleted"}


@router.patch("/{conv_id}", response_model=Conversation)
async def update_conversation(conv_id: str, data: ConversationUpdate):
    """Update conversation title"""

    db = await get_database()

    update_data = {"updated_at": datetime.utcnow()}
    if data.title is not None:
        update_data["title"] = data.title

    # First try to find by 'id' field (UUID), then by '_id' (ObjectId)
    result = await db.conversations.update_one(
        {"id": conv_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        try:
            result = await db.conversations.update_one(
                {"_id": ObjectId(conv_id)},
                {"$set": update_data}
            )
        except Exception:
            pass

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = await db.conversations.find_one({"id": conv_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Remove _id field
    if "_id" in conversation:
        del conversation["_id"]

    return Conversation(**conversation)


@router.get("/{conv_id}/messages", response_model=List[dict])
async def get_messages(conv_id: str):
    """Get all messages from a conversation"""

    db = await get_database()

    try:
        conversation = await db.conversations.find_one({"_id": ObjectId(conv_id)})
    except Exception:
        conversation = await db.conversations.find_one({"id": conv_id})

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation.get("messages", [])
