from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.models.campaign import CampaignStatus
from app.models.application import AssignmentPhase
from app.schemas.deliverable import DeliverableResponse

class CampaignBase(BaseModel):
    title: str
    description: str
    category: str
    budget: float
    location: str | None = None
    platform: str | None = None
    start_date: date
    end_date: date
    requirements: str | None = None

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    budget: float | None = None
    location: str | None = None
    platform: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: CampaignStatus | None = None
    requirements: str | None = None

class BrandBasicInfo(BaseModel):
    company_name: str
    logo: str | None = None
    model_config = ConfigDict(from_attributes=True)

class CampaignResponse(CampaignBase):
    id: int
    brand_id: int
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime
    brand: BrandBasicInfo
    
    model_config = ConfigDict(from_attributes=True)

class InfluencerBasicInfo(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class AssignmentBasicResponse(BaseModel):
    id: int
    influencer_id: int
    current_phase: AssignmentPhase
    influencer: InfluencerBasicInfo
    model_config = ConfigDict(from_attributes=True)

class StatusLogResponse(BaseModel):
    id: int
    from_status: str | None = None
    to_status: str
    note: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CampaignDetailResponse(CampaignResponse):
    """Detailed campaign with nested deliverables, assignments, and logs."""
    deliverables: list[DeliverableResponse] = []
    assignments: list[AssignmentBasicResponse] = []
    status_logs: list[StatusLogResponse] = []
