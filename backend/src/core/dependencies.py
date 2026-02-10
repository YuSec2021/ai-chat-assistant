"""Authentication dependencies for FastAPI routes"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.auth import decode_access_token
from src.models.user import User, UserResponse
from src.db.mongo import get_user_by_id, get_user_by_username

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        User object if authenticated

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    # Extract user_id
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    # Check if user is banned
    if user.get("is_banned", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been banned"
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    return User(**user)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current admin user.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Optional dependency to get user if token is provided.

    Args:
        credentials: Optional HTTP Bearer token credentials

    Returns:
        User object if token provided and valid, None otherwise
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        return None

    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    user = await get_user_by_id(user_id)
    if user is None:
        return None

    return User(**user)


def user_to_response(user: User) -> UserResponse:
    """
    Convert User model to UserResponse (without sensitive data).

    Args:
        user: User object

    Returns:
        UserResponse object
    """
    return UserResponse(
        id=user.id,
        username=user.username,
        subscription_level=user.subscription_level,
        role=user.role,
        is_active=user.is_active,
        is_banned=user.is_banned,
        created_at=user.created_at
    )
