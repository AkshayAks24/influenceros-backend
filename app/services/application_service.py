from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import CampaignApplication, ApplicationStatus, CampaignAssignment, AssignmentPhase
from app.models.notification import Notification, NotificationType
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate


async def get_application_by_influencer_and_campaign(
    db: AsyncSession, influencer_id: int, campaign_id: int
) -> CampaignApplication | None:
    query = select(CampaignApplication).where(
        CampaignApplication.influencer_id == influencer_id,
        CampaignApplication.campaign_id == campaign_id
    )
    result = await db.execute(query)
    return result.scalars().first()


async def create_application(
    db: AsyncSession, influencer_id: int, campaign_id: int, data: ApplicationCreate
) -> CampaignApplication:
    application = CampaignApplication(
        influencer_id=influencer_id,
        campaign_id=campaign_id,
        status=ApplicationStatus.pending,
        **data.model_dump()
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    # Eager load influencer for response
    query = (
        select(CampaignApplication)
        .where(CampaignApplication.id == application.id)
        .options(selectinload(CampaignApplication.influencer))
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_applications_by_campaign(
    db: AsyncSession, campaign_id: int, page: int = 1, limit: int = 20
) -> dict:
    query = (
        select(CampaignApplication)
        .where(CampaignApplication.campaign_id == campaign_id)
        .options(selectinload(CampaignApplication.influencer))
        .order_by(CampaignApplication.created_at.desc())
    )
    
    count_query = select(func.count()).select_from(
        select(CampaignApplication.id)
        .where(CampaignApplication.campaign_id == campaign_id)
        .subquery()
    )
    total = (await db.execute(count_query)).scalar() or 0
    
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }


async def get_application_by_id(db: AsyncSession, application_id: int) -> CampaignApplication | None:
    query = (
        select(CampaignApplication)
        .where(CampaignApplication.id == application_id)
        .options(
            selectinload(CampaignApplication.influencer),
            selectinload(CampaignApplication.campaign)
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


async def update_application_status(
    db: AsyncSession, application: CampaignApplication, status_update: ApplicationStatusUpdate
) -> CampaignApplication:
    if application.status != ApplicationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This application has already been decided and cannot be changed"
        )

    # We expect application to have influencer and campaign eager loaded
    application.status = ApplicationStatus(status_update.status)
    
    # Send Notification
    title = f"Application {status_update.status.capitalize()}"
    message = f"Your application to '{application.campaign.title}' was {status_update.status}!"
    
    notification = Notification(
        user_id=application.influencer.user_id,
        title=title,
        message=message,
        type=NotificationType.campaign_update
    )
    db.add(notification)
    
    if status_update.status == "accepted":
        # Create Assignment
        assignment = CampaignAssignment(
            campaign_id=application.campaign_id,
            influencer_id=application.influencer_id,
            application_id=application.id,
            current_phase=AssignmentPhase.brief_sent
        )
        db.add(assignment)
        
    await db.commit()
    await db.refresh(application)
    
    return application
