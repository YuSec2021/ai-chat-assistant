"""Authentication API routes: register, login, captcha"""

from fastapi import APIRouter, HTTPException, status, Depends
from src.models.user import (
    UserCreate, UserLogin, TokenResponse, CaptchaResponse, UserResponse
)
from src.core.auth import captcha_generator, create_access_token, get_password_hash, verify_password
from src.core.dependencies import get_current_user, user_to_response
from src.db.mongo import (
    create_user, get_user_by_username, update_user_last_login, get_user_by_id
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/captcha", response_model=CaptchaResponse)
async def get_captcha():
    """
    Generate a new captcha image for security.

    Returns:
        CaptchaResponse with captcha_id and base64 encoded image
    """
    captcha_id, image = captcha_generator.generate_captcha()
    return CaptchaResponse(captcha_id=captcha_id, image=image)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user account.

    Requirements:
    - Username: 3-20 characters, alphanumeric + underscore only
    - Password: Min 8 characters, must contain uppercase, lowercase, and number
    - Valid captcha code (optional, if provided will be verified)

    Args:
        user_data: User registration data

    Returns:
        TokenResponse with JWT access token and user info

    Raises:
        HTTPException: If username exists, validation fails, or captcha invalid
    """
    # Verify captcha only if provided (captcha is now optional)
    if user_data.captcha_code and user_data.captcha_id:
        if not captcha_generator.verify_captcha(user_data.captcha_id, user_data.captcha_code):
            logger.warning("Registration failed: invalid captcha", username=user_data.username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired captcha code"
            )

    # Check if username already exists
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        logger.warning("Registration failed: username exists", username=user_data.username)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    # Create user with hashed password
    password_hash = get_password_hash(user_data.password)
    user_doc = await create_user(
        username=user_data.username,
        password_hash=password_hash,
        subscription_level="free",
        role="user"
    )

    logger.info("User registered successfully", user_id=user_doc["id"], username=user_data.username)

    # Generate JWT token
    access_token = create_access_token(data={"sub": user_doc["id"]})

    # Return token and user info
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user_doc["id"],
            username=user_doc["username"],
            subscription_level=user_doc["subscription_level"],
            role=user_doc["role"],
            is_active=user_doc["is_active"],
            is_banned=user_doc["is_banned"],
            created_at=user_doc["created_at"]
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """
    Login with username and password.

    Requirements:
    - Valid username and password
    - Valid captcha code
    - Account must be active and not banned

    Args:
        user_data: User login data

    Returns:
        TokenResponse with JWT access token and user info

    Raises:
        HTTPException: If credentials invalid, captcha invalid, or account banned/inactive
    """
    # Verify captcha first
    if not captcha_generator.verify_captcha(user_data.captcha_id, user_data.captcha_code):
        logger.warning("Login failed: invalid captcha", username=user_data.username)
        # Don't reveal if username exists for security
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Get user
    user = await get_user_by_username(user_data.username)
    if not user:
        logger.warning("Login failed: user not found", username=user_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not verify_password(user_data.password, user["password_hash"]):
        logger.warning("Login failed: invalid password", username=user_data.username, user_id=user["id"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if banned
    if user.get("is_banned", False):
        logger.warning("Login failed: user banned", username=user_data.username, user_id=user["id"])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been banned"
        )

    # Check if active
    if not user.get("is_active", True):
        logger.warning("Login failed: user inactive", username=user_data.username, user_id=user["id"])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Update last login
    await update_user_last_login(user["id"])

    logger.info("User logged in successfully", user_id=user["id"], username=user_data.username)

    # Generate JWT token
    access_token = create_access_token(data={"sub": user["id"]})

    # Return token and user info
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            subscription_level=user["subscription_level"],
            role=user["role"],
            is_active=user["is_active"],
            is_banned=user["is_banned"],
            created_at=user["created_at"]
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        UserResponse with user information
    """
    return user_to_response(current_user)


@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """
    Logout current user.

    Note: JWT tokens are stateless, so actual token revocation
    would require a blacklist (Redis). For now, this is mainly
    for client-side token cleanup.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info("User logged out", user_id=current_user.id)
    return {"message": "Successfully logged out"}
