from fastapi import APIRouter, Depends, HTTPException
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.content import StatusLog
from app.models.notification import Notification, NotificationType
from app.models.campaign import Campaign, CampaignStatus
from app.models.application import AssignmentPhase, CampaignAssignment
from app.schemas.assignment import AssignmentPhaseUpdate, LiveUrlCreate
from app.schemas.campaign import AssignmentBasicResponse
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.influencer_service import get_influencer_profile_by_user_id
from app.services.content_service import get_assignment_by_id

router = APIRouter(tags=["Assignments"])

@router.patch(
    "/{id}/phase",
    response_model=AssignmentBasicResponse,
    summary="Update assignment phase",
    description="""
    Updates the phase of a campaign assignment.
    - `brief_sent` -> `content_creation`: Influencer accepts the brief.
    - `live` -> `completed`: Brand marks the assignment as completed.
    
    If all assignments for a campaign are completed, the overall campaign status is also marked as completed.
    
    **Access Level:** Both Brands and Influencers (role-specific restrictions apply per phase transition)
    
    **Error Codes:**
    - `400 Bad Request`: Invalid phase transition via this endpoint.
    - `403 Forbidden`: The caller is not authorized to update the assignment (e.g., wrong role or not the owner).
    - `404 Not Found`: The assignment was not found.
    - `409 Conflict`: The transition is invalid from the current phase (e.g., trying to complete an assignment that isn't live).
    """
)
async def update_assignment_phase(
    id: int,
    data: AssignmentPhaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    assignment = await get_assignment_by_id(db, id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    old_phase = assignment.current_phase
    new_phase = data.phase

    if current_user.role == UserRole.brand:
        brand = await get_brand_profile_by_user_id(db, current_user.id)
        if not brand or assignment.campaign.brand_id != brand.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this assignment")
    elif current_user.role == UserRole.influencer:
        influencer = await get_influencer_profile_by_user_id(db, current_user.id)
        if not influencer or assignment.influencer_id != influencer.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this assignment")
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    if new_phase == AssignmentPhase.content_creation:
        if current_user.role != UserRole.influencer:
            raise HTTPException(status_code=403, detail="Only influencers can accept the brief")
        if old_phase != AssignmentPhase.brief_sent:
            raise HTTPException(status_code=409, detail=f"Cannot transition to content_creation from {old_phase}")
        note = "Influencer accepted the brief and started content creation."
        
        # Notify the brand
        notif = Notification(
            user_id=assignment.campaign.brand.user_id,
            title="Brief Accepted",
            message=f"Influencer has accepted the brief and started content creation for '{assignment.campaign.title}'.",
            type=NotificationType.campaign_update
        )
        db.add(notif)

    elif new_phase == AssignmentPhase.completed:
        if current_user.role != UserRole.brand:
            raise HTTPException(status_code=403, detail="Only brands can complete assignments")
        if old_phase != AssignmentPhase.live:
            raise HTTPException(status_code=409, detail=f"Cannot transition to completed from {old_phase}")
        note = "Brand marked assignment as completed."
        
        # Notify the influencer
        notif = Notification(
            user_id=assignment.influencer.user_id,
            title="Assignment Completed",
            message=f"Your assignment for '{assignment.campaign.title}' has been marked as completed.",
            type=NotificationType.campaign_update
        )
        db.add(notif)
    else:
        raise HTTPException(status_code=400, detail="Invalid phase transition via this endpoint")

    assignment.current_phase = new_phase
    
    # Insert StatusLog row
    log = StatusLog(
        campaign_id=assignment.campaign_id,
        actor_id=current_user.id,
        from_status=old_phase.value,
        to_status=data.phase.value,
        note=note
    )
    db.add(log)
    
    # Campaign-level completion logic
    if new_phase == AssignmentPhase.completed:
        query = select(CampaignAssignment).where(CampaignAssignment.campaign_id == assignment.campaign_id)
        result = await db.execute(query)
        all_assignments = result.scalars().all()
        
        all_completed = all(a.current_phase == AssignmentPhase.completed or a.id == assignment.id for a in all_assignments)
        if all_completed:
            assignment.campaign.status = CampaignStatus.completed
            campaign_log = StatusLog(
                campaign_id=assignment.campaign_id,
                actor_id=current_user.id,
                from_status=CampaignStatus.in_progress.value,
                to_status=CampaignStatus.completed.value,
                note="All assignments completed. Campaign marked as completed."
            )
            db.add(campaign_log)

    await db.commit()
    await db.refresh(assignment, ["influencer"])
    return assignment

@router.post(
    "/{id}/live-url",
    response_model=AssignmentBasicResponse,
    summary="Submit live post URL",
    description="""
    Submits the URL of the live social media post for an approved assignment.
    This transitions the assignment phase from `approved` to `live`.
    
    **Access Level:** Influencer only (must be the assigned influencer)
    
    **Error Codes:**
    - `400 Bad Request`: The URL is empty or improperly formatted.
    - `403 Forbidden`: The caller is not an influencer, or is not the assigned influencer for this assignment.
    - `404 Not Found`: The assignment was not found.
    - `409 Conflict`: The assignment is not in the `approved` phase.
    """
)
async def submit_live_url(
    id: int,
    data: LiveUrlCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != UserRole.influencer:
        raise HTTPException(status_code=403, detail="Only influencers can submit a live URL")
        
    assignment = await get_assignment_by_id(db, id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    influencer = await get_influencer_profile_by_user_id(db, current_user.id)
    if not influencer or assignment.influencer_id != influencer.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this assignment")
        
    if assignment.current_phase != AssignmentPhase.approved:
        raise HTTPException(status_code=409, detail=f"Cannot submit live URL from {assignment.current_phase}")
        
    if not data.live_url.strip():
        raise HTTPException(status_code=400, detail="Live URL cannot be empty")
        
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
    if not re.match(url_pattern, data.live_url):
        raise HTTPException(status_code=400, detail="Invalid URL format")
        
    old_phase = assignment.current_phase
    assignment.live_url = data.live_url
    assignment.current_phase = AssignmentPhase.live
    
    log = StatusLog(
        campaign_id=assignment.campaign_id,
        actor_id=current_user.id,
        from_status=old_phase.value,
        to_status=AssignmentPhase.live.value,
        note="Influencer posted the content live."
    )
    db.add(log)
    
    # Notifying the brand
    notif = Notification(
        user_id=assignment.campaign.brand.user_id,
        title="Live URL Submitted",
        message=f"Influencer submitted a live post link for '{assignment.campaign.title}'!",
        type=NotificationType.campaign_update
    )
    db.add(notif)
    
    await db.commit()
    await db.refresh(assignment, ["influencer"])
    return assignment
