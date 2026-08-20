from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.brand import BrandProfileResponse, BrandProfileUpdate
from app.services.brand_service import (
    get_brand_profile_by_id,
    get_brand_profile_by_user_id,
    upsert_brand_profile
)

router = APIRouter(tags=["Brands"])


@router.get(
    "/me",
    response_model=BrandProfileResponse,
    summary="Get my brand profile",
    description="""
    Fetches the currently authenticated brand's profile.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not a brand.
    - `404 Not Found`: The brand profile does not exist.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_brand_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand profile not found"
        )
    return profile


@router.put(
    "/profile",
    response_model=BrandProfileResponse,
    summary="Upsert brand profile",
    description="""
    Upserts the currently authenticated brand's profile. Creates it if it doesn't exist, otherwise updates it.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `400 Bad Request`: Missing required fields for brand profile creation (company_name, industry).
    - `403 Forbidden`: The caller is not a brand.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def upsert_profile(
    data: BrandProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        profile = await upsert_brand_profile(db, current_user.id, data)
        return profile
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields for brand profile creation (company_name, industry)"
        )


@router.get(
    "/{id}",
    response_model=BrandProfileResponse,
    summary="Get brand profile details",
    description="""
    Fetch a public brand profile by its ID.
    
    **Access Level:** Public
    
    **Error Codes:**
    - `404 Not Found`: The brand profile was not found.
    """
)
async def get_brand(id: int, db: AsyncSession = Depends(get_db)):
    profile = await get_brand_profile_by_id(db, id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand profile not found"
        )
    return profile
