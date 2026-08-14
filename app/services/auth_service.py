from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by their email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    """
    Register a new user. Checks for email uniqueness, hashes the password,
    and saves the User record to the database.
    """
    existing_user = await get_user_by_email(db, data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    new_user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Authenticate a user by email and password. Returns the User model if valid,
    otherwise returns None.
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
