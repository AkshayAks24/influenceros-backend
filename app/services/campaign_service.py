from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campaign import Campaign, CampaignStatus
from app.models.content import StatusLog
from app.models.application import CampaignAssignment
from app.schemas.campaign import CampaignCreate, CampaignUpdate


async def create_campaign(db: AsyncSession, brand_id: int, data: CampaignCreate) -> Campaign:
    campaign = Campaign(
        brand_id=brand_id,
        status=CampaignStatus.draft,
        **data.model_dump()
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return await get_campaign_by_id(db, campaign.id)


async def get_campaigns(
    db: AsyncSession,
    status: CampaignStatus | None = None,
    category: str | None = None,
    brand_id: int | None = None,
    page: int = 1,
    limit: int = 20
) -> dict:
    query = select(Campaign).options(selectinload(Campaign.brand))
    
    if status:
        query = query.where(Campaign.status == status)
    if category:
        query = query.where(Campaign.category == category)
    if brand_id:
        query = query.where(Campaign.brand_id == brand_id)
        
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(Campaign.created_at.desc()).offset(offset).limit(limit))
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }


async def get_campaign_by_id(db: AsyncSession, campaign_id: int) -> Campaign | None:
    query = (
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .options(
            selectinload(Campaign.brand),
            selectinload(Campaign.deliverables),
            selectinload(Campaign.assignments).selectinload(CampaignAssignment.influencer),
            selectinload(Campaign.status_logs)
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


async def update_campaign(
    db: AsyncSession, campaign: Campaign, actor_id: int, data: CampaignUpdate
) -> Campaign:
    update_data = data.model_dump(exclude_unset=True)
    old_status = campaign.status
    
    for key, value in update_data.items():
        setattr(campaign, key, value)
        
    # Check if status changed
    if "status" in update_data and old_status != campaign.status:
        # Create a StatusLog
        log = StatusLog(
            campaign_id=campaign.id,
            actor_id=actor_id,
            from_status=old_status,
            to_status=campaign.status,
            note=f"Status manually updated to {campaign.status}"
        )
        db.add(log)
        
    await db.commit()
    return await get_campaign_by_id(db, campaign.id)


async def delete_campaign(db: AsyncSession, campaign: Campaign) -> None:
    await db.delete(campaign)
    await db.commit()
