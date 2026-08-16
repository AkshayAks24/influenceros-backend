from datetime import datetime
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campaign import Campaign, CampaignStatus
from app.models.application import CampaignAssignment, CampaignApplication
from app.models.influencer import InfluencerProfile
from app.models.metric_snapshot import MetricSnapshot, OwnerType

async def get_brand_dashboard_stats(db: AsyncSession, brand_id: int):
    # active campaigns
    active_query = select(func.count(Campaign.id)).where(
        Campaign.brand_id == brand_id,
        Campaign.status.in_([CampaignStatus.open, CampaignStatus.in_progress, CampaignStatus.in_review])
    )
    active_campaigns = (await db.execute(active_query)).scalar() or 0
    
    # completed campaigns
    completed_query = select(func.count(Campaign.id)).where(
        Campaign.brand_id == brand_id,
        Campaign.status == CampaignStatus.completed
    )
    completed_campaigns = (await db.execute(completed_query)).scalar() or 0
    
    # total influencers worked with
    influencers_query = (
        select(func.count(distinct(CampaignAssignment.influencer_id)))
        .join(Campaign, Campaign.id == CampaignAssignment.campaign_id)
        .where(Campaign.brand_id == brand_id)
    )
    total_influencers = (await db.execute(influencers_query)).scalar() or 0
    
    # total spending
    spending_query = select(func.sum(Campaign.budget)).where(
        Campaign.brand_id == brand_id,
        Campaign.status.in_([CampaignStatus.completed, CampaignStatus.in_progress, CampaignStatus.in_review])
    )
    total_spending = (await db.execute(spending_query)).scalar() or 0.0
    
    # recent campaigns
    recent_campaigns_query = (
        select(Campaign)
        .where(Campaign.brand_id == brand_id)
        .options(selectinload(Campaign.brand))
        .order_by(Campaign.created_at.desc())
        .limit(5)
    )
    recent_campaigns = (await db.execute(recent_campaigns_query)).scalars().all()
    
    # recommended influencers (not worked with this brand)
    worked_with_subq = (
        select(CampaignAssignment.influencer_id)
        .join(Campaign, Campaign.id == CampaignAssignment.campaign_id)
        .where(Campaign.brand_id == brand_id)
    )
    recommended_query = (
        select(InfluencerProfile)
        .where(InfluencerProfile.id.notin_(worked_with_subq))
        .options(selectinload(InfluencerProfile.user))
        .order_by(InfluencerProfile.trust_score.desc())
        .limit(4)
    )
    recommended_influencers = (await db.execute(recommended_query)).scalars().all()
    
    # reach over time
    reach_query = (
        select(
            func.date_format(MetricSnapshot.recorded_at, "%Y-%m").label("month"),
            func.max(MetricSnapshot.value).label("value")
        )
        .where(
            MetricSnapshot.owner_type == OwnerType.brand,
            MetricSnapshot.owner_id == brand_id,
            MetricSnapshot.metric_name == "reach"
        )
        .group_by("month")
        .order_by("month")
    )
    reach_results = await db.execute(reach_query)
    reach_over_time = [
        {"month": row.month, "value": float(row.value)} for row in reach_results.all()
    ]
    
    return {
        "active_campaigns": active_campaigns,
        "completed_campaigns": completed_campaigns,
        "total_influencers_worked_with": total_influencers,
        "total_spending": float(total_spending),
        "recent_campaigns": list(recent_campaigns),
        "recommended_influencers": list(recommended_influencers),
        "reach_over_time": reach_over_time
    }

async def get_influencer_dashboard_stats(db: AsyncSession, influencer_id: int):
    # profile_completion
    influencer = await db.get(InfluencerProfile, influencer_id)
    profile_completion = influencer.profile_completion if influencer else 0
    
    # active campaigns
    active_campaigns_query = (
        select(Campaign)
        .join(CampaignAssignment, Campaign.id == CampaignAssignment.campaign_id)
        .where(
            CampaignAssignment.influencer_id == influencer_id,
            Campaign.status.notin_([CampaignStatus.completed, CampaignStatus.cancelled, CampaignStatus.draft])
        )
        .options(selectinload(Campaign.brand))
    )
    active_campaigns = (await db.execute(active_campaigns_query)).scalars().all()
    
    # pending invites (approx by pending applications)
    pending_query = select(func.count(CampaignApplication.id)).where(
        CampaignApplication.influencer_id == influencer_id,
        CampaignApplication.status == "pending"
    )
    pending_invites = (await db.execute(pending_query)).scalar() or 0
    
    # earnings logic (MVP approximation)
    assignments_query = (
        select(Campaign.id, Campaign.budget, Campaign.status, Campaign.end_date)
        .join(CampaignAssignment, Campaign.id == CampaignAssignment.campaign_id)
        .where(CampaignAssignment.influencer_id == influencer_id)
    )
    influencer_campaigns = (await db.execute(assignments_query)).all()
    
    total_earnings = 0.0
    this_month_earnings = 0.0
    pending_payout = 0.0
    monthly_earnings_map = {}
    earnings_by_month = []
    
    if influencer_campaigns:
        campaign_ids = [c.id for c in influencer_campaigns]
        
        # count assignments per campaign to split budget
        assignee_counts_query = (
            select(CampaignAssignment.campaign_id, func.count(CampaignAssignment.id))
            .where(CampaignAssignment.campaign_id.in_(campaign_ids))
            .group_by(CampaignAssignment.campaign_id)
        )
        assignee_counts = dict((await db.execute(assignee_counts_query)).all())
        
        current_month = datetime.now().strftime("%Y-%m")
        
        for c in influencer_campaigns:
            count = assignee_counts.get(c.id, 1)
            share = c.budget / count if count > 0 else 0
            
            if c.status == CampaignStatus.completed:
                total_earnings += share
                end_month = c.end_date.strftime("%Y-%m") if c.end_date else current_month
                
                if end_month == current_month:
                    this_month_earnings += share
                
                monthly_earnings_map[end_month] = monthly_earnings_map.get(end_month, 0) + share
            else:
                pending_payout += share
                
        earnings_by_month = [{"month": k, "value": float(v)} for k, v in sorted(monthly_earnings_map.items())]
        
    # follower growth
    follower_query = (
        select(
            func.date_format(MetricSnapshot.recorded_at, "%Y-%m").label("month"),
            func.max(MetricSnapshot.value).label("value")
        )
        .where(
            MetricSnapshot.owner_type == OwnerType.influencer,
            MetricSnapshot.owner_id == influencer_id,
            MetricSnapshot.metric_name == "followers"
        )
        .group_by("month")
        .order_by("month")
    )
    follower_results = await db.execute(follower_query)
    follower_growth = [
        {"month": row.month, "value": float(row.value)} for row in follower_results.all()
    ]
    
    # recommended campaigns
    applied_subq = select(CampaignApplication.campaign_id).where(CampaignApplication.influencer_id == influencer_id)
    assigned_subq = select(CampaignAssignment.campaign_id).where(CampaignAssignment.influencer_id == influencer_id)
    
    rec_camp_query = (
        select(Campaign)
        .where(
            Campaign.status == CampaignStatus.open,
            Campaign.id.notin_(applied_subq),
            Campaign.id.notin_(assigned_subq)
        )
        .options(selectinload(Campaign.brand))
    )
    
    cat = influencer.category if influencer else ""
    if cat:
        rec_camp_query = rec_camp_query.where(Campaign.category == cat)
        
    rec_camp_query = rec_camp_query.order_by(Campaign.created_at.desc()).limit(4)
    recommended_campaigns = (await db.execute(rec_camp_query)).scalars().all()
    
    return {
        "profile_completion": profile_completion,
        "active_campaigns": list(active_campaigns),
        "pending_invites": pending_invites,
        "total_earnings": total_earnings,
        "this_month_earnings": this_month_earnings,
        "pending_payout": pending_payout,
        "earnings_by_month": earnings_by_month,
        "follower_growth": follower_growth,
        "recommended_campaigns": list(recommended_campaigns)
    }
