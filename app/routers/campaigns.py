from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user, get_current_user_optional, require_role
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
    description="""
    Creates a new campaign for the authenticated brand.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not a brand.
    """,
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
    description="""
    Adds a new deliverable requirement (e.g., TikTok Video, Instagram Post) to an existing campaign.
    
    **Access Level:** Brand only (must own the campaign)
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not a brand, or does not own the campaign.
    - `404 Not Found`: The campaign was not found.
    """,
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
    description="""
    Submits an application from an influencer to a specific open campaign.
    
    **Access Level:** Influencer only
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not an influencer.
    - `404 Not Found`: The campaign was not found.
    - `409 Conflict`: The campaign is not open for applications, or the influencer has already applied.
    """,
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
        
    if campaign.status != CampaignStatus.open:
        raise HTTPException(status_code=409, detail="This campaign is not currently accepting applications")
        
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
    description="""
    Retrieves a paginated list of all applications for a specific campaign.
    
    **Access Level:** Brand only (must own the campaign)
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not a brand, or does not own the campaign.
    - `404 Not Found`: The campaign was not found.
    """,
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
    summary="Get campaign activity log",
    description="""
    Retrieves the activity log (status changes, review actions, etc.) for a campaign.
    
    **Access Level:** Brand (must own campaign) or Influencer (must be assigned to the campaign)
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not authorized to view the activity log for this campaign.
    - `404 Not Found`: The campaign was not found.
    """
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
    summary="List campaigns",
    description="""
    Retrieves a paginated list of public campaigns. If an authenticated brand calls this, it may include their own draft campaigns.
    
    **Access Level:** Public / Any authenticated user
    
    **Error Codes:** None specific to this endpoint.
    """
)
async def list_campaigns(
    status: CampaignStatus | None = None,
    category: str | None = Query(None, description="Filter by category"),
    brand_id: int | None = Query(None, description="Filter by brand"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    current_brand_id = None
    if current_user and current_user.role == "brand":
        brand = await get_brand_profile_by_user_id(db, current_user.id)
        if brand:
            current_brand_id = brand.id
            
    return await get_campaigns(db, status, category, brand_id, page, limit, current_brand_id)


@router.get(
    "/{id}",
    response_model=CampaignDetailResponse,
    summary="Get campaign details",
    description="""
    Retrieves detailed information about a specific campaign, including deliverables and assignments.
    Draft campaigns are only visible to the brand that owns them.
    
    **Access Level:** Public / Any authenticated user (with ownership restrictions for drafts)
    
    **Error Codes:**
    - `404 Not Found`: The campaign was not found, or it is a draft owned by someone else.
    """
)
async def get_campaign(id: int, current_user: User | None = Depends(get_current_user_optional), db: AsyncSession = Depends(get_db)):
    campaign = await get_campaign_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if campaign.status == CampaignStatus.draft:
        is_owner = False
        if current_user and current_user.role == "brand":
            brand = await get_brand_profile_by_user_id(db, current_user.id)
            if brand and campaign.brand_id == brand.id:
                is_owner = True
                
        if not is_owner:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
    return campaign


@router.put(
    "/{id}",
    response_model=CampaignDetailResponse,
    summary="Update a campaign",
    description="""
    Updates the details or status of an existing campaign.
    
    **Access Level:** Brand only (must own the campaign)
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not a brand, or does not own the campaign.
    - `404 Not Found`: The campaign was not found.
    """,
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
    description="""
    Permanently deletes a campaign. 
    
    **Access Level:** Brand only (must own the campaign)
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not a brand, or does not own the campaign.
    - `404 Not Found`: The campaign was not found.
    - `409 Conflict`: The campaign cannot be deleted because it has active assignments (should be cancelled instead).
    """,
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
        
    if campaign.assignments:
        raise HTTPException(status_code=409, detail="Cannot delete a campaign with active assignments. Please set the status to cancelled instead.")
        
    await delete_campaign(db, campaign)
    return None
