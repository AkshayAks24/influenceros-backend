from pydantic import BaseModel

class InfluencerMatchResponse(BaseModel):
    influencer_id: int
    match_score: int
    reason: str

class CampaignSuggestionRequest(BaseModel):
    category: str

class CampaignSuggestionResponse(BaseModel):
    suggestions: list[str]

class ProfileInsightResponse(BaseModel):
    insights: list[str]
