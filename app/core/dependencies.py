"""
FastAPI dependencies (e.g., database session, current user).
"""
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency that extracts the JWT token, decodes it, and fetches the User from the database.
    Raises an HTTP 401 Unauthorized if the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
        
    return user


def require_role(*roles: str) -> Callable:
    """
    Dependency factory that enforces specific role(s).
    Raises an HTTP 403 Forbidden if the current user's role is not in the allowed roles list.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
        
    return role_checker
