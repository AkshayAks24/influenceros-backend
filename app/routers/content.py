from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.content import ContentComment
from app.schemas.content import SubmittedContentCreate, SubmittedContentResponse, ContentReviewRequest
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.brand_service import get_brand_profile_by_user_id
from app.services.influencer_service import get_influencer_profile_by_user_id
from app.services.content_service import (
    get_assignment_by_id,
    submit_content,
    get_assignment_contents,
    get_content_by_id,
    review_content,
    add_content_comment,
    get_content_comments
)

router = APIRouter(tags=["Content"])

@router.post(
    "/assignments/{id}/content",
    response_model=SubmittedContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit content for an assignment"
)
async def create_content_submission(
    id: int,
    data: SubmittedContentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "influencer":
        raise HTTPException(status_code=403, detail="Only influencers can submit content")
        
    influencer = await get_influencer_profile_by_user_id(db, current_user.id)
    if not influencer:
        raise HTTPException(status_code=403, detail="Influencer profile required")
        
    assignment = await get_assignment_by_id(db, id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    if assignment.influencer_id != influencer.id:
        raise HTTPException(status_code=403, detail="Not authorized to submit content for this assignment")
        
    return await submit_content(db, assignment, data)


@router.get(
    "/assignments/{id}/content",
    response_model=list[SubmittedContentResponse],
    summary="List content for an assignment"
)
async def list_assignment_content(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    assignment = await get_assignment_by_id(db, id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    # Verify permissions: current user must be the assigned influencer or the owning brand
    authorized = False
    if current_user.role == "influencer":
        influencer = await get_influencer_profile_by_user_id(db, current_user.id)
        if influencer and assignment.influencer_id == influencer.id:
            authorized = True
    elif current_user.role == "brand":
        brand = await get_brand_profile_by_user_id(db, current_user.id)
        if brand and assignment.campaign.brand_id == brand.id:
            authorized = True
            
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to view this assignment's content")
        
    return await get_assignment_contents(db, id)


@router.patch(
    "/content/{id}/review",
    response_model=SubmittedContentResponse,
    summary="Review submitted content"
)
async def review_submitted_content(
    id: int,
    data: ContentReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "brand":
        raise HTTPException(status_code=403, detail="Only brands can review content")
        
    content = await get_content_by_id(db, id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
        
    brand = await get_brand_profile_by_user_id(db, current_user.id)
    if not brand or content.assignment.campaign.brand_id != brand.id:
        raise HTTPException(status_code=403, detail="Not authorized to review this content")
        
    # If the brand left a review note, append it as a ContentComment immediately
    if data.note:
        comment = ContentComment(
            content_id=content.id,
            author_id=current_user.id,
            comment=data.note
        )
        db.add(comment)
        
    return await review_content(db, content, data)


@router.post(
    "/content/{id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to submitted content"
)
async def create_content_comment(
    id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    content = await get_content_by_id(db, id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
        
    authorized = False
    if current_user.role == "brand":
        brand = await get_brand_profile_by_user_id(db, current_user.id)
        if brand and content.assignment.campaign.brand_id == brand.id:
            authorized = True
    elif current_user.role == "influencer":
        influencer = await get_influencer_profile_by_user_id(db, current_user.id)
        if influencer and content.assignment.influencer_id == influencer.id:
            authorized = True
            
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to comment on this content")
        
    return await add_content_comment(db, content.id, current_user.id, data.comment)


@router.get(
    "/content/{id}/comments",
    response_model=list[CommentResponse],
    summary="List comments for submitted content"
)
async def list_content_comments(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    content = await get_content_by_id(db, id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
        
    authorized = False
    if current_user.role == "brand":
        brand = await get_brand_profile_by_user_id(db, current_user.id)
        if brand and content.assignment.campaign.brand_id == brand.id:
            authorized = True
    elif current_user.role == "influencer":
        influencer = await get_influencer_profile_by_user_id(db, current_user.id)
        if influencer and content.assignment.influencer_id == influencer.id:
            authorized = True
            
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to view comments for this content")
        
    return await get_content_comments(db, content.id)
