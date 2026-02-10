"""Admin API routes: user management, subscription management"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from src.models.user import UserResponse, UserUpdate
from src.core.dependencies import get_current_admin_user, user_to_response
from src.db.mongo import list_users, update_user, ban_user, unban_user, get_user_by_id
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=dict)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search by username"),
    current_user = Depends(get_current_admin_user)
):
    """
    Get list of all users (Admin only).

    Args:
        skip: Pagination offset
        limit: Maximum users to return
        search: Optional search string for username
        current_user: Current admin user

    Returns:
        Dict with users list and total count

    Raises:
        HTTPException: If user is not admin
    """
    logger.info("Admin fetching users", admin_id=current_user.id)

    users, total = await list_users(skip=skip, limit=limit, search=search)

    return {
        "users": [UserResponse(**user) for user in users],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user = Depends(get_current_admin_user)
):
    """
    Get a specific user by ID (Admin only).

    Args:
        user_id: User UUID
        current_user: Current admin user

    Returns:
        UserResponse with user information

    Raises:
        HTTPException: If user not found or current user is not admin
    """
    logger.info("Admin fetching user", admin_id=current_user.id, target_user_id=user_id)

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(**user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: str,
    updates: UserUpdate,
    current_user = Depends(get_current_admin_user)
):
    """
    Update user information (Admin only).

    Can update:
    - subscription_level: "free", "gold", or "diamond"
    - is_banned: true or false (cannot ban yourself)

    Args:
        user_id: User UUID to update
        updates: Fields to update
        current_user: Current admin user

    Returns:
        Updated UserResponse

    Raises:
        HTTPException: If user not found, trying to ban self, or not admin
    """
    # Check if user exists
    target_user = await get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from banning themselves
    if user_id == current_user.id and updates.is_banned is not None and updates.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot ban your own account"
        )

    logger.info(
        "Admin updating user",
        admin_id=current_user.id,
        target_user_id=user_id,
        updates=updates.model_dump(exclude_unset=True)
    )

    # Build update dict
    update_data = {}
    if updates.subscription_level is not None:
        update_data["subscription_level"] = updates.subscription_level
    if updates.is_banned is not None:
        update_data["is_banned"] = updates.is_banned

    # Update user
    updated_user = await update_user(user_id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

    logger.info(
        "User updated successfully",
        admin_id=current_user.id,
        target_user_id=user_id
    )

    return UserResponse(**updated_user)


@router.post("/users/{user_id}/ban")
async def ban_user_account(
    user_id: str,
    current_user = Depends(get_current_admin_user)
):
    """
    Ban a user account (Admin only).

    Args:
        user_id: User UUID to ban
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found, trying to ban self, or not admin
    """
    # Prevent admin from banning themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot ban your own account"
        )

    logger.info("Admin banning user", admin_id=current_user.id, target_user_id=user_id)

    # Check if user exists
    target_user = await get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Ban user
    success = await ban_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user"
        )

    logger.info("User banned successfully", admin_id=current_user.id, target_user_id=user_id)

    return {"message": "User banned successfully"}


@router.post("/users/{user_id}/unban")
async def unban_user_account(
    user_id: str,
    current_user = Depends(get_current_admin_user)
):
    """
    Unban a user account (Admin only).

    Args:
        user_id: User UUID to unban
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or not admin
    """
    logger.info("Admin unbanning user", admin_id=current_user.id, target_user_id=user_id)

    # Check if user exists
    target_user = await get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Unban user
    success = await unban_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unban user"
        )

    logger.info("User unbanned successfully", admin_id=current_user.id, target_user_id=user_id)

    return {"message": "User unbanned successfully"}
