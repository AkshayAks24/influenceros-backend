from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brand import BrandProfile
from app.schemas.brand import BrandProfileUpdate


async def get_brand_profile_by_id(db: AsyncSession, brand_id: int) -> BrandProfile | None:
    """Fetch a brand profile by its ID, eager loading the associated user."""
    query = (
        select(BrandProfile)
        .where(BrandProfile.id == brand_id)
        .options(selectinload(BrandProfile.user))
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_brand_profile_by_user_id(db: AsyncSession, user_id: int) -> BrandProfile | None:
    """Fetch a brand profile by the user ID, eager loading the associated user."""
    query = (
        select(BrandProfile)
        .where(BrandProfile.user_id == user_id)
        .options(selectinload(BrandProfile.user))
    )
    result = await db.execute(query)
    return result.scalars().first()


async def upsert_brand_profile(
    db: AsyncSession, user_id: int, data: BrandProfileUpdate
) -> BrandProfile:
    """
    Creates the brand profile if it doesn't exist, otherwise updates it.
    Raises IntegrityError if creation is attempted without required fields.
    """
    profile = await get_brand_profile_by_user_id(db, user_id)
    
    if not profile:
        # Create new profile
        profile = BrandProfile(
            user_id=user_id,
            **data.model_dump(exclude_unset=True)
        )
        db.add(profile)
    else:
        # Update existing profile
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
            
    # Commit changes (may raise IntegrityError if required fields are missing on creation)
    await db.commit()
    await db.refresh(profile)
    
    # Reload with relationships
    return await get_brand_profile_by_user_id(db, user_id)
