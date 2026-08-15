from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deliverable import Deliverable
from app.models.application import CampaignAssignment
from app.schemas.deliverable import DeliverableCreate

async def create_deliverable(db: AsyncSession, campaign_id: int, data: DeliverableCreate) -> Deliverable:
    item = Deliverable(campaign_id=campaign_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

async def get_deliverable_by_id(db: AsyncSession, deliverable_id: int) -> Deliverable | None:
    query = select(Deliverable).where(Deliverable.id == deliverable_id).options(selectinload(Deliverable.campaign))
    result = await db.execute(query)
    return result.scalars().first()

async def toggle_deliverable_completion(db: AsyncSession, deliverable: Deliverable) -> Deliverable:
    deliverable.is_completed = not deliverable.is_completed
    deliverable.completed_at = datetime.now(timezone.utc) if deliverable.is_completed else None
    await db.commit()
    await db.refresh(deliverable)
    return deliverable

async def is_influencer_assigned_to_campaign(db: AsyncSession, influencer_id: int, campaign_id: int) -> bool:
    query = select(CampaignAssignment).where(
        CampaignAssignment.campaign_id == campaign_id,
        CampaignAssignment.influencer_id == influencer_id
    )
    result = await db.execute(query)
    return result.scalars().first() is not None
