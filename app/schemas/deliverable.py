from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DeliverableCreate(BaseModel):
    description: str

class DeliverableResponse(BaseModel):
    id: int
    campaign_id: int
    description: str
    is_completed: bool
    completed_at: datetime | None = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
