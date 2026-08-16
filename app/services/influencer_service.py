from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.influencer import InfluencerProfile, VerificationStatus
from app.models.review import Review
from app.schemas.influencer import InfluencerProfileCreate, InfluencerProfileUpdate


async def get_influencers(
    db: AsyncSession,
    search: str | None = None,
    category: str | None = None,
    location: str | None = None,
    platform: str | None = None,
    min_followers: int | None = None,
    max_followers: int | None = None,
    min_engagement: float | None = None,
    verified_only: bool = False,
    sort_by: Literal["followers", "engagement_rate", "trust_score"] = "followers",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = 1,
    limit: int = 20,
) -> dict:
    """
    Builds and executes an optimized query to fetch a paginated, filtered list 
    of influencers for the discovery grid.
    """
    
    # Eager load the user relationship since InfluencerListItem needs it for the avatar
    query = select(InfluencerProfile).options(selectinload(InfluencerProfile.user))
    
    # 1. Apply Filters Conditionally
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                InfluencerProfile.username.ilike(search_term),
                InfluencerProfile.bio.ilike(search_term),
                InfluencerProfile.category.ilike(search_term),
            )
        )
        
    if category:
        query = query.where(InfluencerProfile.category == category)
        
    if location:
        query = query.where(InfluencerProfile.location.ilike(f"%{location}%"))
        
    if platform:
        if platform not in ["instagram", "youtube", "tiktok"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}. Must be instagram, youtube, or tiktok."
            )
        # Use MySQL json_extract to check if the platform key exists in the JSON object
        query = query.where(
            func.json_extract(InfluencerProfile.platforms, f'$.{platform}').is_not(None)
        )
        
    if min_followers is not None:
        query = query.where(InfluencerProfile.follower_count >= min_followers)
        
    if max_followers is not None:
        query = query.where(InfluencerProfile.follower_count <= max_followers)
        
    if min_engagement is not None:
        query = query.where(InfluencerProfile.engagement_rate >= min_engagement)
        
    if verified_only:
        query = query.where(InfluencerProfile.verification_status == VerificationStatus.verified)
        
    # 2. Count Total Matching Records
    # Using a subquery guarantees accurate counts regardless of JOINs
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 3. Apply Sorting
    order_col = {
        "followers": InfluencerProfile.follower_count,
        "engagement_rate": InfluencerProfile.engagement_rate,
        "trust_score": InfluencerProfile.trust_score,
    }.get(sort_by, InfluencerProfile.follower_count)
    
    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())
        
    # 4. Apply Pagination (Offset/Limit)
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # 5. Execute and Return
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }


async def get_influencer_by_id(db: AsyncSession, influencer_id: int) -> InfluencerProfile | None:
    """Fetch an influencer by ID with user, portfolios, and reviews eagerly loaded."""
    query = (
        select(InfluencerProfile)
        .where(InfluencerProfile.id == influencer_id)
        .options(
            selectinload(InfluencerProfile.user),
            selectinload(InfluencerProfile.portfolios),
            selectinload(InfluencerProfile.reviews).selectinload(Review.brand)
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


def compute_profile_completion(profile: InfluencerProfile) -> int:
    """Computes the profile completion percentage (0-100)."""
    score = 0
    total_criteria = 6
    
    if profile.bio and str(profile.bio).strip():
        score += 1
    if profile.category and str(profile.category).strip():
        score += 1
    if profile.location and str(profile.location).strip():
        score += 1
    if profile.platforms and isinstance(profile.platforms, dict) and len(profile.platforms) > 0:
        score += 1
    if profile.pricing and isinstance(profile.pricing, list) and len(profile.pricing) > 0:
        score += 1
    if getattr(profile, "portfolios", None) and len(profile.portfolios) > 0:
        score += 1
        
    return int((score / total_criteria) * 100)


async def get_influencer_profile_by_user_id(db: AsyncSession, user_id: int) -> InfluencerProfile | None:
    """Fetch an influencer's own profile by their user_id, eager loading relationships."""
    query = (
        select(InfluencerProfile)
        .where(InfluencerProfile.user_id == user_id)
        .options(
            selectinload(InfluencerProfile.user),
            selectinload(InfluencerProfile.portfolios),
            selectinload(InfluencerProfile.reviews).selectinload(Review.brand)
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


async def create_influencer_profile(
    db: AsyncSession, user_id: int, data: InfluencerProfileCreate
) -> InfluencerProfile | None:
    """Creates a new InfluencerProfile for the user. Returns None if one already exists."""
    existing = await get_influencer_profile_by_user_id(db, user_id)
    if existing:
        return None

    new_profile = InfluencerProfile(
        user_id=user_id,
        **data.model_dump()
    )
    new_profile.profile_completion = compute_profile_completion(new_profile)
    
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    
    return await get_influencer_profile_by_user_id(db, user_id)


async def update_influencer_profile(
    db: AsyncSession, user_id: int, data: InfluencerProfileUpdate
) -> InfluencerProfile | None:
    """Updates an existing InfluencerProfile. Returns None if it doesn't exist."""
    profile = await get_influencer_profile_by_user_id(db, user_id)
    if not profile:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    profile.profile_completion = compute_profile_completion(profile)
    
    await db.commit()
    await db.refresh(profile)
    
    return await get_influencer_profile_by_user_id(db, user_id)
