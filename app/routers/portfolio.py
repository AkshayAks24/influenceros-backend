from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.influencer import PortfolioItemCreate, PortfolioItemResponse
from app.services.influencer_service import get_influencer_profile_by_user_id
from app.services.portfolio_service import create_portfolio_item, get_portfolio_item, delete_portfolio_item

router = APIRouter(tags=["Portfolio"])

@router.post(
    "",
    response_model=PortfolioItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add portfolio item",
    description="""
    Adds a new item (e.g., media file or external link) to the authenticated influencer's portfolio.
    
    **Access Level:** Influencer only
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not an influencer.
    - `404 Not Found`: The influencer profile was not found.
    """,
    dependencies=[Depends(require_role("influencer"))]
)
async def add_portfolio_item(
    data: PortfolioItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_influencer_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Influencer profile not found")
        
    return await create_portfolio_item(db, profile.id, data)

@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete portfolio item",
    description="""
    Deletes a specific portfolio item from the authenticated influencer's portfolio.
    
    **Access Level:** Influencer only (must own the item)
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not an influencer, or does not own the portfolio item.
    - `404 Not Found`: The influencer profile or portfolio item was not found.
    """,
    dependencies=[Depends(require_role("influencer"))]
)
async def remove_portfolio_item(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_influencer_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Influencer profile not found")
        
    item = await get_portfolio_item(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
        
    if item.influencer_id != profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this item")
        
    await delete_portfolio_item(db, item)
    return None
