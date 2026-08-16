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
    dependencies=[Depends(get_current_user)]
)
async def match_influencers(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_influencer_matches(db, campaign_id)

@router.post(
    "/campaign-suggestions",
    response_model=CampaignSuggestionResponse,
    summary="Get AI-powered campaign content suggestions",
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
