from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

from app.models.content import ContentStatus

class SubmittedContentCreate(BaseModel):
    media_url: str
    caption: str | None = None

class ContentReviewRequest(BaseModel):
    decision: Literal["approved", "changes_requested"]
    note: str | None = None

class SubmittedContentResponse(BaseModel):
    id: int
    assignment_id: int
    media_url: str
    caption: str | None = None
    status: ContentStatus
    submitted_at: datetime
    reviewed_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)
