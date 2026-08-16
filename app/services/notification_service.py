from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationType

async def get_notifications(
    db: AsyncSession, 
    user_id: int, 
    type: NotificationType | None = None, 
    unread_only: bool = False,
    page: int = 1,
    limit: int = 20
) -> dict:
    query = select(Notification).where(Notification.user_id == user_id)
    
    if type:
        query = query.where(Notification.type == type)
    if unread_only:
        query = query.where(Notification.is_read == False)
        
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.order_by(Notification.created_at.desc())
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    
    return {
        "items": result.scalars().all(),
        "total": total,
        "page": page,
        "limit": limit
    }

async def get_notification_by_id(db: AsyncSession, id: int) -> Notification | None:
    query = select(Notification).where(Notification.id == id)
    result = await db.execute(query)
    return result.scalars().first()

async def mark_notification_as_read(db: AsyncSession, notification: Notification) -> Notification:
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification

async def mark_all_as_read(db: AsyncSession, user_id: int):
    query = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.execute(query)
    await db.commit()
