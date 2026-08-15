from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.models.content import StatusLog
from app.schemas.assignment import AssignmentPhaseUpdate
from app.schemas.campaign import AssignmentBasicResponse
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.content_service import get_assignment_by_id

router = APIRouter(tags=["Assignments"])

@router.patch(
    "/{id}/phase",
    response_model=AssignmentBasicResponse,
    summary="Update assignment phase",
    dependencies=[Depends(require_role("brand"))]
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
        
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand or assignment.campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this assignment")
        
    old_phase = assignment.current_phase
    assignment.current_phase = data.phase
    
    # Insert StatusLog row
    log = StatusLog(
        campaign_id=assignment.campaign_id,
        actor_id=current_user.id,
        from_status=old_phase.value,
        to_status=data.phase.value,
        note="Assignment phase updated"
    )
    db.add(log)
    
    await db.commit()
    # Ensure nested influencer is re-loaded for AssignmentBasicResponse
    await db.refresh(assignment, ["influencer"])
    return assignment
