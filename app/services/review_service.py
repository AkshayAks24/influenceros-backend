from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.review import Review
from app.schemas.influencer import ReviewCreate

async def create_review(
    db: AsyncSession, brand_id: int, influencer_id: int, data: ReviewCreate
) -> Review:
    review = Review(
        brand_id=brand_id,
        influencer_id=influencer_id,
        **data.model_dump()
    )
    db.add(review)
    await db.commit()
    
    # Reload with brand relationship
    query = select(Review).where(Review.id == review.id).options(selectinload(Review.brand))
    result = await db.execute(query)
    return result.scalars().first()

async def get_reviews_by_influencer(
    db: AsyncSession, influencer_id: int, page: int = 1, limit: int = 20
) -> dict:
    query = (
        select(Review)
        .where(Review.influencer_id == influencer_id)
        .options(selectinload(Review.brand))
        .order_by(Review.created_at.desc())
    )
    
    count_query = select(func.count()).select_from(
        select(Review.id).where(Review.influencer_id == influencer_id).subquery()
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
