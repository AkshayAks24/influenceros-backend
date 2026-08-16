from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.pricing_plan import PricingPlan
from app.schemas.pricing_plan import PricingPlanResponse

router = APIRouter(tags=["Pricing"])

@router.get(
    "/pricing-plans",
    response_model=list[PricingPlanResponse],
    summary="Get all pricing plans"
)
async def list_pricing_plans(db: AsyncSession = Depends(get_db)):
    query = select(PricingPlan).order_by(PricingPlan.price.asc())
    result = await db.execute(query)
    return result.scalars().all()
