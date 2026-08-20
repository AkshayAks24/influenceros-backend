from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.ai import (
    InfluencerMatchResponse, 
    CampaignSuggestionRequest, 
    CampaignSuggestionResponse, 
    ProfileInsightResponse
)
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.campaign_service import get_campaign_by_id
from app.services.influencer_service import get_influencer_profile_by_user_id
from app.services.ai_service import (
    get_influencer_matches, 
    get_campaign_suggestions, 
    get_profile_insights
)

router = APIRouter(tags=["AI Integration"])

@router.get(
    "/influencer-match",
    response_model=list[InfluencerMatchResponse],
    summary="Get AI-powered influencer matches for a campaign",
    description="""
    Retrieves a list of suggested influencers for a specific campaign using AI matching.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `403 Forbidden`: The caller does not have a brand profile, or they do not own the specified campaign.
    - `404 Not Found`: The specified campaign was not found.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def match_influencers(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand:
        raise HTTPException(status_code=403, detail="Brand profile required")
        
    campaign = await get_campaign_by_id(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to match influencers for a campaign you do not own")
        
    return await get_influencer_matches(db, campaign_id)

@router.post(
    "/campaign-suggestions",
    response_model=CampaignSuggestionResponse,
    summary="Get AI-powered campaign content suggestions",
    description="""
    Generates AI-powered campaign content ideas and suggestions based on a given category.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `422 Unprocessable Entity`: The request body is invalid.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def suggest_campaign_ideas(
    data: CampaignSuggestionRequest
):
    suggestions = get_campaign_suggestions(data.category)
    return {"suggestions": suggestions}

@router.get(
    "/profile-insights",
    response_model=ProfileInsightResponse,
    summary="Get AI-powered profile insights",
    description="""
    Analyzes the influencer's profile data and provides AI-generated insights for growth.
    
    **Access Level:** Influencer only
    
    **Error Codes:**
    - `403 Forbidden`: The caller does not have an active influencer profile.
    """,
    dependencies=[Depends(require_role("influencer"))]
)
async def profile_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    influencer = await get_influencer_profile_by_user_id(db, current_user.id)
    if not influencer:
        raise HTTPException(status_code=403, detail="Influencer profile required")
        
    insights = get_profile_insights(influencer)
    return {"insights": insights}
