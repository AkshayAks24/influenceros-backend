from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.notification import NotificationType

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedNotificationResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    limit: int
