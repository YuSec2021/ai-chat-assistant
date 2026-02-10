"""User models for authentication and subscription management"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
import re


class SubscriptionLevel:
    """Subscription level constants"""
    FREE = "free"
    GOLD = "gold"
    DIAMOND = "diamond"

    @classmethod
    def all(cls):
        return [cls.FREE, cls.GOLD, cls.DIAMOND]


class UserRole:
    """User role constants"""
    USER = "user"
    ADMIN = "admin"

    @classmethod
    def all(cls):
        return [cls.USER, cls.ADMIN]


class User(BaseModel):
    """User model"""

    id: str = Field(description="User UUID")
    username: str = Field(description="Username (unique)")
    password_hash: str = Field(description="Argon2 hashed password")
    subscription_level: Literal["free", "gold", "diamond"] = Field(
        default=SubscriptionLevel.FREE,
        description="Subscription level"
    )
    role: Literal["user", "admin"] = Field(
        default=UserRole.USER,
        description="User role"
    )
    is_active: bool = Field(default=True, description="Account active status")
    is_banned: bool = Field(default=False, description="Account banned status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")


class UserCreate(BaseModel):
    """Request model for user registration"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Username (alphanumeric and underscore only)"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 characters)"
    )
    captcha_code: str = Field(default="", min_length=0, max_length=6, description="Captcha code (optional)")
    captcha_id: str = Field(default="", description="Captcha session ID (optional)")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format (alphanumeric and underscore only, no special characters)"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError(
                'Username can only contain letters, numbers, and underscores'
            )
        # Check for XSS/NoSQL injection patterns
        dangerous_patterns = ['<', '>', '"', "'", '&', '$', '{', '}', '(', ')']
        if any(pattern in v for pattern in dangerous_patterns):
            raise ValueError('Username contains invalid characters')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        # Check for dangerous characters
        dangerous_patterns = ['<', '>', '"', "'", '&']
        if any(pattern in v for pattern in dangerous_patterns):
            raise ValueError('Password contains invalid characters')
        return v

    @field_validator('captcha_code')
    @classmethod
    def validate_captcha(cls, v: str) -> str:
        """Validate captcha code format"""
        if not re.match(r'^[A-Z0-9]+$', v.upper()):
            raise ValueError('Invalid captcha format')
        return v.upper()


class UserLogin(BaseModel):
    """Request model for user login"""

    username: str = Field(..., min_length=3, max_length=20, description="Username")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    captcha_code: str = Field(..., min_length=4, max_length=6, description="Captcha code")
    captcha_id: str = Field(..., description="Captcha session ID")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate and sanitize username"""
        dangerous_patterns = ['<', '>', '"', "'", '&', '$', '{', '}', '(', ')']
        if any(pattern in v for pattern in dangerous_patterns):
            raise ValueError('Username contains invalid characters')
        return v

    @field_validator('captcha_code')
    @classmethod
    def validate_captcha(cls, v: str) -> str:
        """Validate captcha code format"""
        if not re.match(r'^[A-Z0-9]+$', v.upper()):
            raise ValueError('Invalid captcha format')
        return v.upper()


class UserResponse(BaseModel):
    """Response model for user data (without sensitive info)"""

    id: str = Field(description="User UUID")
    username: str = Field(description="Username")
    subscription_level: Literal["free", "gold", "diamond"] = Field(description="Subscription level")
    role: Literal["user", "admin"] = Field(description="User role")
    is_active: bool = Field(description="Account active status")
    is_banned: bool = Field(description="Account banned status")
    created_at: datetime = Field(description="Account creation timestamp")


class UserUpdate(BaseModel):
    """Request model for updating user (admin only)"""

    subscription_level: Optional[Literal["free", "gold", "diamond"]] = Field(
        default=None,
        description="New subscription level"
    )
    is_banned: Optional[bool] = Field(default=None, description="Ban status")


class TokenResponse(BaseModel):
    """Response model for JWT token"""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(description="User information")


class CaptchaResponse(BaseModel):
    """Response model for captcha"""

    captcha_id: str = Field(description="Captcha session ID")
    image: str = Field(description="Base64 encoded PNG image")
