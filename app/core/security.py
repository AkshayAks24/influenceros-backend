"""
Security related utility functions (hashing, JWT).
"""
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plaintext password against a hashed password."""
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Creates a JWT access token encoding the given data dictionary.
    Sets expiration based on settings if expires_delta is not provided.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes a JWT access token and returns its payload.
    Raises a ValueError if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid or expired token: {str(e)}")
