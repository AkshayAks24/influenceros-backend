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
    summary="Register a new user",
    description="""
    Register a new brand or influencer account.
    Returns the newly created user data and a fresh JWT access token.
    
    **Access Level:** Public (Unauthenticated)
    
    **Error Codes:**
    - `400 Bad Request`: Validation error in the request payload, or email already registered.
    """
)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
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
    summary="Login and get token",
    description="""
    Authenticate a user with their email and password.
    Returns the user data and a fresh JWT access token.
    
    **Access Level:** Public (Unauthenticated)
    
    **Error Codes:**
    - `401 Unauthorized`: Incorrect email or password.
    """
)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, request.email, request.password)
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
    summary="Get current user profile",
    description="""
    Fetch the currently authenticated user's details.
    
    **Access Level:** Any authenticated user
    
    **Error Codes:**
    - `401 Unauthorized`: Missing or invalid JWT access token.
    """
)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
