from datetime import datetime
from pydantic import BaseModel, ConfigDict

class FavoriteCreate(BaseModel):
    influencer_id: int

class FavoriteResponse(BaseModel):
    id: int
    brand_id: int
    influencer_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
