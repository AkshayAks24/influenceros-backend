from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new brand or influencer account.
    Returns the newly created user data and a fresh JWT access token.
    """
    user = await register_user(db, request)
    
    # Generate JWT containing user ID and role
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value if hasattr(user.role, 'value') else user.role}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get token"
)
async def login(request: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user with their email (in the username field) and password.
    Returns the user data and a fresh JWT access token.
    """
    user = await authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value if hasattr(user.role, 'value') else user.role}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Fetch the currently authenticated user's details.
    """
    return UserResponse.model_validate(current_user)
