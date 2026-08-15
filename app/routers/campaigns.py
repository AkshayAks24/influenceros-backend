from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.models.campaign import CampaignStatus
from app.models.application import CampaignApplication, ApplicationStatus, CampaignAssignment
from app.models.content import StatusLog
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse, CampaignDetailResponse, StatusLogResponse
from app.schemas.deliverable import DeliverableCreate, DeliverableResponse
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.influencer_service import get_influencer_profile_by_user_id
from app.services.campaign_service import (
    create_campaign,
    get_campaigns,
    get_campaign_by_id,
    update_campaign,
    delete_campaign
)
from app.services.deliverable_service import create_deliverable
from app.services.application_service import (
    create_application,
    get_application_by_influencer_and_campaign,
    get_applications_by_campaign
)

router = APIRouter(tags=["Campaigns"])


class PaginatedCampaignResponse(BaseModel):
    items: list[CampaignResponse]
    total: int
    page: int
    limit: int


class PaginatedApplicationResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
    page: int
    limit: int


@router.post(
    "",
    response_model=CampaignDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new campaign",
    dependencies=[Depends(require_role("brand"))]
)
async def create_new_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand:
        raise HTTPException(status_code=403, detail="Brand profile required to create campaigns")
        
    return await create_campaign(db, brand.id, data)


@router.post(
    "/{id}/deliverables",
    response_model=DeliverableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a deliverable to a campaign",
    dependencies=[Depends(require_role("brand"))]
)
async def add_deliverable(
    id: int,
    data: DeliverableCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = await get_campaign_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand or campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this campaign")
        
    return await create_deliverable(db, id, data)


@router.post(
    "/{id}/apply",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a campaign",
    dependencies=[Depends(require_role("influencer"))]
)
async def apply_to_campaign(
    id: int,
    data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = await get_campaign_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    influencer = await get_influencer_profile_by_user_id(db, current_user.id)
    if not influencer:
        raise HTTPException(status_code=403, detail="Influencer profile required to apply")
        
    existing = await get_application_by_influencer_and_campaign(db, influencer.id, id)
    if existing:
        raise HTTPException(status_code=409, detail="You have already applied to this campaign")
        
    return await create_application(db, influencer.id, id, data)


@router.get(
    "/{id}/applications",
    response_model=PaginatedApplicationResponse,
    summary="Get campaign applications",
    dependencies=[Depends(require_role("brand"))]
)
async def get_campaign_applications(
    id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = await get_campaign_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand or campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these applications")
        
    return await get_applications_by_campaign(db, id, page, limit)


@router.get(
    "/{id}/activity-log",
    response_model=list[StatusLogResponse],
    summary="Get campaign activity log"
)
async def get_campaign_activity_log(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = await get_campaign_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    authorized = False
    if current_user.role == "brand":
        brand = await get_brand_profile_by_user_id(db, current_user.id)
        if brand and campaign.brand_id == brand.id:
            authorized = True
    elif current_user.role == "influencer":
        influencer = await get_influencer_profile_by_user_id(db, current_user.id)
        if influencer:
            query = select(CampaignAssignment).where(
                CampaignAssignment.campaign_id == id,
                CampaignAssignment.influencer_id == influencer.id
            )
            result = await db.execute(query)
            if result.scalars().first():
                authorized = True
                
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to view this campaign's activity log")
        
    query = (
        select(StatusLog)
        .where(StatusLog.campaign_id == id)
        .order_by(StatusLog.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "",
    response_model=PaginatedCampaignResponse,
    summary="List campaigns"
)
async def list_campaigns(
    status: CampaignStatus | None = None,
    category: str | None = Query(None, description="Filter by category"),
    brand_id: int | None = Query(None, description="Filter by brand"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    return await get_campaigns(db, status, category, brand_id, page, limit)


@router.get(
    "/{id}",
    response_model=CampaignDetailResponse,
    summary="Get campaign details"
)
async def get_campaign(id: int, db: AsyncSession = Depends(get_db)):
    campaign = await get_campaign_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put(
    "/{id}",
    response_model=CampaignDetailResponse,
    summary="Update a campaign",
    dependencies=[Depends(require_role("brand"))]
)
async def edit_campaign(
    id: int,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = await get_campaign_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand or campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this campaign")
        
    return await update_campaign(db, campaign, current_user.id, data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a campaign",
    dependencies=[Depends(require_role("brand"))]
)
async def remove_campaign(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = await get_campaign_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand or campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this campaign")
        
    await delete_campaign(db, campaign)
    return None
