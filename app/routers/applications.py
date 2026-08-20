from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.application import ApplicationStatusUpdate, ApplicationResponse
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.application_service import get_application_by_id, update_application_status

router = APIRouter(tags=["Applications"])

@router.put(
    "/{id}/status",
    response_model=ApplicationResponse,
    summary="Update application status",
    description="""
    Accepts or rejects an influencer's application for a campaign.
    If accepted, it automatically creates a CampaignAssignment and notifies the influencer.
    If rejected, it simply updates the status and notifies the influencer.
    
    **Access Level:** Brand only
    
    **Error Codes:**
    - `403 Forbidden`: The caller is not a brand, or does not own the campaign associated with the application.
    - `404 Not Found`: The application was not found.
    """,
    dependencies=[Depends(require_role("brand"))]
)
async def update_status(
    id: int,
    data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Accept or reject an application.
    If accepted, automatically creates a CampaignAssignment and notifies the influencer.
    If rejected, simply updates status and notifies the influencer.
    Must be the brand that owns the campaign.
    """
    application = await get_application_by_id(db, id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
        
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand or application.campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this application")
        
    if application.status == data.status:
        return application
        
    return await update_application_status(db, application, data, current_user.id)
