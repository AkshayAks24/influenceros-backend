from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus
from app.schemas.campaign import InfluencerBasicInfo

class ApplicationCreate(BaseModel):
    proposal: str
    proposed_price: float | None = None

class ApplicationStatusUpdate(BaseModel):
    status: Literal["accepted", "rejected"]

class ApplicationResponse(BaseModel):
    id: int
    campaign_id: int
    influencer_id: int
    proposal: str
    proposed_price: float | None = None
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
    influencer: InfluencerBasicInfo
    
    model_config = ConfigDict(from_attributes=True)
