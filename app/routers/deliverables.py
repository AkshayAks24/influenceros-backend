from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.deliverable import DeliverableResponse
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.influencer_service import get_influencer_profile_by_user_id
from app.services.deliverable_service import get_deliverable_by_id, toggle_deliverable_completion, is_influencer_assigned_to_campaign

router = APIRouter(tags=["Deliverables"])

@router.patch(
    "/{id}/toggle",
    response_model=DeliverableResponse,
    summary="Toggle deliverable completion status"
)
async def toggle_deliverable(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggles the is_completed state of a deliverable.
    Only the brand owning the campaign, or an influencer officially assigned to it, can do this.
    """
    deliverable = await get_deliverable_by_id(db, id)
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")
        
    campaign_id = deliverable.campaign_id
    
    # Check permissions: must be owning brand OR assigned influencer
    authorized = False
    
    if current_user.role == "brand":
        brand = await get_brand_profile_by_user_id(db, current_user.id)
        if brand and deliverable.campaign.brand_id == brand.id:
            authorized = True
            
    elif current_user.role == "influencer":
        influencer = await get_influencer_profile_by_user_id(db, current_user.id)
        if influencer:
            is_assigned = await is_influencer_assigned_to_campaign(db, influencer.id, campaign_id)
            if is_assigned:
                authorized = True
                
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to modify this deliverable")
        
    return await toggle_deliverable_completion(db, deliverable)
