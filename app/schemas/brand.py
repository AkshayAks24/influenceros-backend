from pydantic import BaseModel, ConfigDict
from app.schemas.auth import UserResponse

class BrandProfileBase(BaseModel):
    company_name: str
    industry: str
    logo: str | None = None
    description: str | None = None
    location: str | None = None
    website: str | None = None
    company_size: str | None = None


class BrandProfileCreate(BrandProfileBase):
    """Schema for creating a new Brand Profile."""
    pass


class BrandProfileUpdate(BaseModel):
    """Schema for updating an existing Brand Profile. All fields are optional."""
    company_name: str | None = None
    industry: str | None = None
    logo: str | None = None
    description: str | None = None
    location: str | None = None
    website: str | None = None
    company_size: str | None = None


class BrandProfileResponse(BrandProfileBase):
    """Full Brand Profile details including nested user information."""
    id: int
    user_id: int
    user: UserResponse
    
    model_config = ConfigDict(from_attributes=True)
