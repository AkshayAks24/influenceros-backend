from pydantic import BaseModel, ConfigDict
from app.schemas.campaign import CampaignResponse
from app.schemas.influencer import InfluencerListItem

class MonthValueData(BaseModel):
    month: str
    value: float

class BrandDashboardResponse(BaseModel):
    active_campaigns: int
    completed_campaigns: int
    total_influencers_worked_with: int
    total_spending: float
    recent_campaigns: list[CampaignResponse]
    recommended_influencers: list[InfluencerListItem]
    reach_over_time: list[MonthValueData]
    
    model_config = ConfigDict(from_attributes=True)

class InfluencerDashboardResponse(BaseModel):
    profile_completion: int
    active_campaigns: list[CampaignResponse]
    pending_invites: int
    total_earnings: float
    this_month_earnings: float
    pending_payout: float
    earnings_by_month: list[MonthValueData]
    follower_growth: list[MonthValueData]
    recommended_campaigns: list[CampaignResponse]
    
    model_config = ConfigDict(from_attributes=True)
