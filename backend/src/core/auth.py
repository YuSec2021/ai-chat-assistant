"""Authentication utilities: JWT, password hashing, and captcha"""

import base64
import io
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4

import jwt
from passlib.context import CryptContext
from captcha.image import ImageCaptcha
from PIL import Image

from src.config import settings


# Password hashing context using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT configuration
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, settings.api_key, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.api_key, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


class CaptchaGenerator:
    """
    Generate and validate captcha images for security.
    """

    def __init__(self, width: int = 160, height: int = 60):
        """
        Initialize captcha generator.

        Args:
            width: Image width in pixels
            height: Image height in pixels
        """
        self.width = width
        self.height = height
        self.image_captcha = ImageCaptcha(width=width, height=height)
        # Store captcha codes in memory (in production, use Redis)
        self._storage: Dict[str, Dict[str, Any]] = {}

    def generate_captcha(self) -> tuple[str, str]:
        """
        Generate a new captcha image and code.

        Returns:
            Tuple of (captcha_id, base64_encoded_image)
        """
        # Generate random 4-character code (uppercase letters and numbers)
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        captcha_id = str(uuid4())

        # Generate captcha image
        image = self.image_captcha.generate_image(code)

        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Store captcha code with expiration (5 minutes)
        self._storage[captcha_id] = {
            'code': code,
            'expires_at': datetime.utcnow() + timedelta(minutes=5)
        }

        # Clean up expired captchas
        self._cleanup_expired()

        return captcha_id, f"data:image/png;base64,{image_base64}"

    def verify_captcha(self, captcha_id: str, code: str) -> bool:
        """
        Verify a captcha code.

        Args:
            captcha_id: Captcha session ID
            code: User-provided captcha code

        Returns:
            True if code matches and not expired, False otherwise
        """
        if captcha_id not in self._storage:
            return False

        stored_data = self._storage[captcha_id]

        # Check expiration
        if datetime.utcnow() > stored_data['expires_at']:
            del self._storage[captcha_id]
            return False

        # Verify code (case-insensitive)
        is_valid = stored_data['code'].upper() == code.upper()

        # Remove captcha after verification (one-time use)
        del self._storage[captcha_id]

        return is_valid

    def _cleanup_expired(self):
        """Remove expired captchas from storage."""
        now = datetime.utcnow()
        expired_ids = [
            captcha_id
            for captcha_id, data in self._storage.items()
            if now > data['expires_at']
        ]
        for captcha_id in expired_ids:
            del self._storage[captcha_id]


# Global captcha generator instance
captcha_generator = CaptchaGenerator()
