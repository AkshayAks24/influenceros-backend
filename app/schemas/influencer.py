from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, computed_field, Field

from app.models.influencer import VerificationStatus
from app.schemas.auth import UserResponse

class InfluencerProfileBase(BaseModel):
    username: str
    category: str
    bio: str | None = None
    location: str | None = None
    languages: list[str] = []
    platforms: dict[str, Any] = {}
    follower_count: int = 0
    engagement_rate: float = 0.0
    audience_quality_score: float = 0.0
    trust_score: float = 0.0
    trust_score_breakdown: dict[str, float] = {}
    profile_completion: int = 0
    pricing: list[dict[str, Any]] = []
    verification_status: VerificationStatus = VerificationStatus.unverified


class InfluencerProfileCreate(InfluencerProfileBase):
    """Schema for creating a new Influencer Profile."""
    pass


class InfluencerProfileUpdate(BaseModel):
    """Schema for updating an existing Influencer Profile. All fields are optional."""
    username: str | None = None
    category: str | None = None
    bio: str | None = None
    location: str | None = None
    languages: list[str] | None = None
    platforms: dict[str, Any] | None = None
    follower_count: int | None = None
    engagement_rate: float | None = None
    audience_quality_score: float | None = None
    trust_score: float | None = None
    trust_score_breakdown: dict[str, float] | None = None
    profile_completion: int | None = None
    pricing: list[dict[str, Any]] | None = None
    verification_status: VerificationStatus | None = None


class InfluencerProfileResponse(InfluencerProfileBase):
    """Full Influencer Profile details including nested user information."""
    id: int
    user_id: int
    user: UserResponse
    
    model_config = ConfigDict(from_attributes=True)


class InfluencerListItem(BaseModel):
    """Light-weight Influencer model for the Discovery grid."""
    id: int
    username: str
    category: str
    location: str | None = None
    follower_count: int
    engagement_rate: float
    trust_score: float
    verification_status: VerificationStatus
    user: UserResponse
    
    @computed_field
    @property
    def avatar(self) -> str | None:
        """Expose the user's profile image directly as 'avatar' for the grid UI."""
        return self.user.profile_image if self.user else None
        
    model_config = ConfigDict(from_attributes=True)


class PortfolioItemResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    campaign_name: str | None = None
    brand_name: str | None = None
    media_url: str | None = None
    campaign_result: str | None = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReviewBrandResponse(BaseModel):
    company_name: str
    logo: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    id: int
    rating: int
    comment: str | None = None
    created_at: datetime
    brand: ReviewBrandResponse
    
    model_config = ConfigDict(from_attributes=True)


class InfluencerDetailResponse(InfluencerProfileResponse):
    """Detailed influencer profile with portfolios and reviews."""
    portfolios: list[PortfolioItemResponse] = []
    reviews: list[ReviewResponse] = []


class PortfolioItemCreate(BaseModel):
    title: str
    description: str | None = None
    campaign_name: str | None = None
    brand_name: str | None = None
    media_url: str | None = None
    campaign_result: str | None = None


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None
    campaign_id: int | None = None
