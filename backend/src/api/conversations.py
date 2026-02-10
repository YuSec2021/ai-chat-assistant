"""Conversations API endpoints with user isolation"""

from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from src.models.conversation import Conversation, ConversationCreate, ConversationUpdate
from src.models.user import User
from src.core.dependencies import get_current_user
from src.db.mongo import (
    get_user_conversations,
    create_conversation,
    get_conversation_for_user
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=List[Conversation])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    List all conversations for the current user.

    Args:
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return
        current_user: Authenticated user

    Returns:
        List of conversations belonging to the user
    """
    logger.info("Fetching conversations", user_id=current_user.id)

    conversations = await get_user_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    return [Conversation(**conv) for conv in conversations]


@router.post("", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new conversation for the current user.

    Args:
        data: Conversation creation data
        current_user: Authenticated user

    Returns:
        Created conversation
    """
    logger.info("Creating conversation", user_id=current_user.id, title=data.title)

    conversation = await create_conversation(
        user_id=current_user.id,
        title=data.title
    )

    logger.info("Conversation created", conv_id=conversation["id"], user_id=current_user.id)

    return Conversation(**conversation)


@router.get("/{conv_id}", response_model=Conversation)
async def get_conversation(
    conv_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific conversation (with user ownership check).

    Args:
        conv_id: Conversation UUID
        current_user: Authenticated user

    Returns:
        Conversation if user has access

    Raises:
        HTTPException: If conversation not found or user doesn't have access
    """
    logger.info("Fetching conversation", conv_id=conv_id, user_id=current_user.id)

    conversation = await get_conversation_for_user(conv_id, current_user.id)

    if not conversation:
        logger.warning("Conversation not found or access denied", conv_id=conv_id, user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return Conversation(**conversation)


@router.delete("/{conv_id}")
async def delete_conversation(
    conv_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation (with user ownership check).

    Args:
        conv_id: Conversation UUID
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If conversation not found or user doesn't have access
    """
    logger.info("Deleting conversation", conv_id=conv_id, user_id=current_user.id)

    # Check ownership first
    conversation = await get_conversation_for_user(conv_id, current_user.id)
    if not conversation:
        logger.warning("Delete failed: conversation not found or access denied", conv_id=conv_id, user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Delete the conversation
    from src.db.mongo import mongodb
    db = mongodb.get_db()
    result = await db.conversations.delete_one({
        "id": conv_id,
        "user_id": current_user.id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    logger.info("Conversation deleted", conv_id=conv_id, user_id=current_user.id)

    return {"message": "Conversation deleted"}


@router.patch("/{conv_id}", response_model=Conversation)
async def update_conversation(
    conv_id: str,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update conversation title (with user ownership check).

    Args:
        conv_id: Conversation UUID
        data: Update data
        current_user: Authenticated user

    Returns:
        Updated conversation

    Raises:
        HTTPException: If conversation not found or user doesn't have access
    """
    logger.info("Updating conversation", conv_id=conv_id, user_id=current_user.id)

    # Check ownership first
    conversation = await get_conversation_for_user(conv_id, current_user.id)
    if not conversation:
        logger.warning("Update failed: conversation not found or access denied", conv_id=conv_id, user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Update the conversation
    from src.db.mongo import mongodb
    from datetime import datetime

    db = mongodb.get_db()
    update_data = {"updated_at": datetime.utcnow()}
    if data.title is not None:
        update_data["title"] = data.title

    result = await db.conversations.update_one(
        {"id": conv_id, "user_id": current_user.id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Fetch updated conversation
    updated_conversation = await get_conversation_for_user(conv_id, current_user.id)

    logger.info("Conversation updated", conv_id=conv_id, user_id=current_user.id)

    return Conversation(**updated_conversation)


@router.get("/{conv_id}/messages", response_model=List[dict])
async def get_messages(
    conv_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all messages from a conversation (with user ownership check).

    Args:
        conv_id: Conversation UUID
        current_user: Authenticated user

    Returns:
        List of messages

    Raises:
        HTTPException: If conversation not found or user doesn't have access
    """
    logger.info("Fetching messages", conv_id=conv_id, user_id=current_user.id)

    conversation = await get_conversation_for_user(conv_id, current_user.id)

    if not conversation:
        logger.warning("Messages fetch failed: conversation not found or access denied", conv_id=conv_id, user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return conversation.get("messages", [])
