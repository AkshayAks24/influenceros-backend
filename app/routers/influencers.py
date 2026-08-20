from typing import Literal

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.influencer import InfluencerListItem, InfluencerDetailResponse, InfluencerProfileCreate, InfluencerProfileUpdate
from app.services.influencer_service import (
    get_influencers, 
    get_influencer_by_id,
    create_influencer_profile,
    update_influencer_profile,
    get_influencer_profile_by_user_id
)

router = APIRouter(tags=["Influencers"])


class PaginatedInfluencerResponse(BaseModel):
    items: list[InfluencerListItem]
    total: int
    page: int
    limit: int


@router.get(
    "", 
    response_model=PaginatedInfluencerResponse, 
    summary="Discover influencers",
    description="""
    Retrieves a paginated list of influencers for the discovery grid, with optional filtering and sorting.
    
    **Access Level:** Public / Any authenticated user
    
    **Error Codes:** None specific to this endpoint.
    """
)
async def discover_influencers(
    search: str | None = Query(None, description="Search by username, bio, or category"),
    category: str | None = Query(None, description="Filter by category"),
    location: str | None = Query(None, description="Filter by location"),
    platform: str | None = Query(None, description="Filter by platform presence (e.g. instagram, youtube)"),
    min_followers: int | None = Query(None, description="Minimum followers"),
    max_followers: int | None = Query(None, description="Maximum followers"),
    min_engagement: float | None = Query(None, description="Minimum engagement rate"),
    verified_only: bool = Query(False, description="Only show verified influencers"),
    sort_by: Literal["followers", "engagement_rate", "trust_score"] = Query("followers"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a paginated list of influencers for the discovery grid, with optional filtering and sorting.
    """
    result = await get_influencers(
        db=db,
        search=search,
        category=category,
        location=location,
        platform=platform,
        min_followers=min_followers,
        max_followers=max_followers,
        min_engagement=min_engagement,
        verified_only=verified_only,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit
    )
    return result


@router.post(
    "/profile",
    response_model=InfluencerDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create influencer profile",
    description="""
    Creates the current influencer's public profile.
    
    **Access Level:** Influencer only
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not an influencer.
    - `409 Conflict`: A profile already exists for this user.
    """,
    dependencies=[Depends(require_role("influencer"))]
)
async def create_profile(
    data: InfluencerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile = await create_influencer_profile(db, current_user.id, data)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists for this user"
        )
    return profile


@router.put(
    "/profile",
    response_model=InfluencerDetailResponse,
    summary="Update influencer profile",
    description="""
    Updates the current influencer's public profile.
    
    **Access Level:** Influencer only
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not an influencer.
    - `404 Not Found`: The influencer profile was not found.
    """,
    dependencies=[Depends(require_role("influencer"))]
)
async def update_profile(
    data: InfluencerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile = await update_influencer_profile(db, current_user.id, data)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile


@router.get(
    "/me",
    response_model=InfluencerDetailResponse,
    summary="Get my influencer profile",
    description="""
    Fetches the currently authenticated influencer's profile details.
    
    **Access Level:** Influencer only
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not an influencer.
    - `404 Not Found`: The influencer profile was not found.
    """,
    dependencies=[Depends(require_role("influencer"))]
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_influencer_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile


@router.get(
    "/{id}",
    response_model=InfluencerDetailResponse,
    summary="Get influencer details",
    description="""
    Fetches a detailed influencer profile including portfolios and reviews.
    
    **Access Level:** Public / Any authenticated user
    
    **Error Codes:**
    - `404 Not Found`: The influencer was not found.
    """
)
async def get_influencer(id: int, db: AsyncSession = Depends(get_db)):
    influencer = await get_influencer_by_id(db, id)
    if not influencer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Influencer not found"
        )
    return influencer
