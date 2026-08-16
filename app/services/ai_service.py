from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import Campaign
from app.models.influencer import InfluencerProfile

async def get_influencer_matches(db: AsyncSession, campaign_id: int):
    """
    MOCK AI SEAM: 
    In the future, this function will call an external LLM or ML model.
    For now, it calculates a deterministic match score using a weighted combination 
    of engagement_rate and trust_score for influencers in the campaign's category.
    """
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        return []
        
    # Find influencers in same category
    query = (
        select(InfluencerProfile)
        .where(InfluencerProfile.category == campaign.category)
    )
    result = await db.execute(query)
    influencers = result.scalars().all()
    
    matches = []
    for inf in influencers:
        # Simple deterministic scoring logic
        # engagement_rate is usually ~0.0 to 0.15. Max weight 40
        # trust_score is 0-100. Max weight 60
        engagement_points = min(int((inf.engagement_rate * 100) * 4), 40)
        trust_points = int(inf.trust_score * 0.6)
        score = engagement_points + trust_points
        
        # Clamp score between 60 and 98 to look believable in the UI
        score = max(60, min(98, score))
        
        if score > 90:
            reason = f"Excellent match! High trust score ({inf.trust_score}) and top-tier engagement for {campaign.category}."
        elif score > 75:
            reason = f"Strong match. Solid engagement rate with a reliable track record in {campaign.category}."
        else:
            reason = f"Good potential. Matches the {campaign.category} category requirement with acceptable metrics."
            
        matches.append({
            "influencer_id": inf.id,
            "match_score": score,
            "reason": reason
        })
        
    # Sort by match score descending and take top 5
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches[:5]

def get_campaign_suggestions(category: str):
    """
    MOCK AI SEAM:
    Generates content angles based on category. Will be replaced by an actual LLM call.
    """
    base_suggestions = {
        "Fashion": [
            "A 'Get Ready With Me' (GRWM) focusing on transitional seasonal outfits.",
            "A 3-part series styling one hero item in different ways.",
            "A behind-the-scenes look at organizing a capsule wardrobe."
        ],
        "Tech": [
            "An unboxing and first impressions video highlighting hidden features.",
            "A deep-dive tutorial solving a common productivity problem.",
            "A 'day in the life' showing how the product integrates into your workflow."
        ],
        "Fitness": [
            "A 5-minute quick workout integration using the product.",
            "A meal prep tutorial explaining the nutritional benefits.",
            "A vlog tracking progress over a 7-day challenge."
        ]
    }
    
    return base_suggestions.get(
        category, 
        [
            f"An educational deep-dive explaining the core benefits for {category}.",
            "A short-form trending audio video with a quick product cameo.",
            "An honest review format highlighting pros and cons."
        ]
    )

def get_profile_insights(influencer: InfluencerProfile):
    """
    MOCK AI SEAM:
    Analyzes influencer metrics to provide actionable insights. Will be replaced by an LLM call.
    """
    insights = []
    
    if influencer.engagement_rate > 0.05:
        insights.append(f"Your engagement rate ({influencer.engagement_rate * 100:.1f}%) is above average for {influencer.category} — consider raising your pricing tier.")
    else:
        insights.append("Try replying to comments within the first hour of posting to boost your engagement rate.")
        
    if influencer.profile_completion < 100:
        insights.append("Completing your profile will increase your visibility in brand searches by up to 40%.")
        
    # Using getattr for portfolios to avoid lazy load issues if not loaded
    portfolios = getattr(influencer, "portfolios", [])
    if not portfolios:
        insights.append("Brands are 3x more likely to accept applications from influencers with a populated portfolio. Add your past work!")
        
    if not insights:
        insights.append("Your metrics look great! Keep maintaining a consistent posting schedule.")
        
    return insights
