from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.favorite import Favorite
from app.models.influencer import InfluencerProfile

async def get_favorite(db: AsyncSession, brand_id: int, influencer_id: int) -> Favorite | None:
    query = select(Favorite).where(
        Favorite.brand_id == brand_id,
        Favorite.influencer_id == influencer_id
    )
    result = await db.execute(query)
    return result.scalars().first()

async def create_favorite(db: AsyncSession, brand_id: int, influencer_id: int) -> Favorite:
    favorite = Favorite(brand_id=brand_id, influencer_id=influencer_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite

async def delete_favorite(db: AsyncSession, favorite: Favorite):
    await db.delete(favorite)
    await db.commit()

async def get_favorited_influencers(db: AsyncSession, brand_id: int) -> list[InfluencerProfile]:
    query = (
        select(InfluencerProfile)
        .join(Favorite, Favorite.influencer_id == InfluencerProfile.id)
        .where(Favorite.brand_id == brand_id)
        .options(selectinload(InfluencerProfile.user))
        .order_by(Favorite.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
