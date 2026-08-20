from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.favorite import FavoriteCreate, FavoriteResponse
from app.schemas.influencer import InfluencerListItem
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.influencer_service import get_influencer_by_id
from app.services.favorite_service import (
    get_favorite,
    create_favorite,
    delete_favorite,
    get_favorited_influencers
)

router = APIRouter(tags=["Favorites"])

@router.post(
    "",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an influencer to favorites",
    description="""
    Adds a specific influencer to the authenticated brand's favorites list.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `403 Forbidden`: The caller does not have an active brand profile.
    - `404 Not Found`: The specified influencer does not exist.
    - `409 Conflict`: The influencer is already in the brand's favorites.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def add_favorite(
    data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand:
        raise HTTPException(status_code=403, detail="Brand profile required")
        
    influencer = await get_influencer_by_id(db, data.influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
        
    existing = await get_favorite(db, brand.id, data.influencer_id)
    if existing:
        raise HTTPException(status_code=409, detail="Influencer already favorited")
        
    return await create_favorite(db, brand.id, data.influencer_id)

@router.delete(
    "/{influencer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an influencer from favorites",
    description="""
    Removes a specific influencer from the authenticated brand's favorites list.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `403 Forbidden`: The caller does not have an active brand profile.
    - `404 Not Found`: The influencer is not in the brand's favorites.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def remove_favorite(
    influencer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand:
        raise HTTPException(status_code=403, detail="Brand profile required")
        
    favorite = await get_favorite(db, brand.id, influencer_id)
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
        
    await delete_favorite(db, favorite)
    return None

@router.get(
    "",
    response_model=list[InfluencerListItem],
    summary="Get favorited influencers",
    description="""
    Retrieves a list of all influencers favorited by the authenticated brand.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `403 Forbidden`: The caller does not have an active brand profile.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand:
        raise HTTPException(status_code=403, detail="Brand profile required")
        
    return await get_favorited_influencers(db, brand.id)
