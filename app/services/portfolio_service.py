from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.portfolio import Portfolio
from app.schemas.influencer import PortfolioItemCreate

async def create_portfolio_item(db: AsyncSession, influencer_id: int, data: PortfolioItemCreate) -> Portfolio:
    item = Portfolio(influencer_id=influencer_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

async def get_portfolio_item(db: AsyncSession, portfolio_id: int) -> Portfolio | None:
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    return result.scalars().first()

async def delete_portfolio_item(db: AsyncSession, item: Portfolio) -> None:
    await db.delete(item)
    await db.commit()
