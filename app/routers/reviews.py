from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.influencer import ReviewCreate, ReviewResponse
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.influencer_service import get_influencer_by_id
from app.services.campaign_service import get_campaign_by_id
from app.services.review_service import create_review, get_reviews_by_influencer
from app.services.deliverable_service import is_influencer_assigned_to_campaign

router = APIRouter(tags=["Reviews"])

class PaginatedReviewResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    limit: int

@router.post(
    "/influencers/{id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review",
    dependencies=[Depends(require_role("brand"))]
)
async def add_review(
    id: int,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")
        
    influencer = await get_influencer_by_id(db, id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
        
    campaign = await get_campaign_by_id(db, data.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to review an influencer for a campaign you do not own")
        
    is_assigned = await is_influencer_assigned_to_campaign(db, influencer.id, campaign.id)
    if not is_assigned:
        raise HTTPException(status_code=403, detail="Influencer was not assigned to this campaign")
        
    return await create_review(db, brand.id, id, data)

@router.get(
    "/influencers/{id}/reviews",
    response_model=PaginatedReviewResponse,
    summary="Get influencer reviews"
)
async def list_reviews(
    id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    return await get_reviews_by_influencer(db, id, page, limit)
