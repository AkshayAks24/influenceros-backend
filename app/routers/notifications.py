from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.notification import NotificationResponse, PaginatedNotificationResponse
from app.services.notification_service import (
    get_notifications,
    get_notification_by_id,
    mark_notification_as_read,
    mark_all_as_read
)

router = APIRouter(tags=["Notifications"])

@router.get(
    "",
    response_model=PaginatedNotificationResponse,
    summary="Get user notifications",
    description="""
    Retrieves a paginated list of notifications for the authenticated user, optionally filtered by type or read status.
    
    **Access Level:** Any authenticated user
    
    **Error Codes:** None specific to this endpoint.
    """
)
async def list_notifications(
    type: NotificationType | None = None,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_notifications(db, current_user.id, type, unread_only, page, limit)

@router.patch(
    "/read-all",
    summary="Mark all notifications as read",
    description="""
    Marks all unread notifications as read for the authenticated user.
    
    **Access Level:** Any authenticated user
    
    **Error Codes:** None specific to this endpoint.
    """
)
async def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}

@router.patch(
    "/{id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read",
    description="""
    Marks a specific notification as read.
    
    **Access Level:** Any authenticated user
    
    **Error Codes:**
    - `403 Forbidden`: The caller does not own the specified notification.
    - `404 Not Found`: The notification was not found.
    """
)
async def read_notification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    notification = await get_notification_by_id(db, id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this notification")
        
    return await mark_notification_as_read(db, notification)
