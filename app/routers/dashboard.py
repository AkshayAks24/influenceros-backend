from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.dashboard import BrandDashboardResponse, InfluencerDashboardResponse
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.influencer_service import get_influencer_profile_by_user_id
from app.services.dashboard_service import get_brand_dashboard_stats, get_influencer_dashboard_stats

router = APIRouter(tags=["Dashboard"])

@router.get(
    "/brand",
    response_model=BrandDashboardResponse,
    summary="Get brand dashboard statistics",
    description="""
    Retrieves aggregated dashboard statistics and active campaign data for the authenticated brand.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `403 Forbidden`: The caller does not have an active brand profile.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def get_brand_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand:
        raise HTTPException(status_code=403, detail="Brand profile required")
        
    stats = await get_brand_dashboard_stats(db, brand.id)
    return stats

@router.get(
    "/influencer",
    response_model=InfluencerDashboardResponse,
    summary="Get influencer dashboard statistics",
    description="""
    Retrieves aggregated dashboard statistics and active assignment data for the authenticated influencer.
    
    **Access Level:** Influencer only
    
    **Error Codes:**
    - `403 Forbidden`: The caller does not have an active influencer profile.
    """,
    dependencies=[Depends(require_role("influencer"))]
)
async def get_influencer_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    influencer = await get_influencer_profile_by_user_id(db, current_user.id)
    if not influencer:
        raise HTTPException(status_code=403, detail="Influencer profile required")
        
    stats = await get_influencer_dashboard_stats(db, influencer.id)
    return stats
