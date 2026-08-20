from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content import SubmittedContent, ContentStatus, ContentComment
from app.models.application import CampaignAssignment, AssignmentPhase
from app.models.campaign import Campaign
from app.models.notification import Notification, NotificationType
from app.schemas.content import SubmittedContentCreate, ContentReviewRequest


async def get_assignment_by_id(db: AsyncSession, assignment_id: int) -> CampaignAssignment | None:
    query = (
        select(CampaignAssignment)
        .where(CampaignAssignment.id == assignment_id)
        .options(
            selectinload(CampaignAssignment.campaign).selectinload(Campaign.brand),
            selectinload(CampaignAssignment.influencer)
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


async def submit_content(
    db: AsyncSession, assignment: CampaignAssignment, data: SubmittedContentCreate, actor_id: int
) -> SubmittedContent:
    if assignment.current_phase != AssignmentPhase.content_creation:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=f"Cannot submit content from {assignment.current_phase}")

    content = SubmittedContent(
        assignment_id=assignment.id,
        status=ContentStatus.pending_review,
        **data.model_dump()
    )
    db.add(content)
    
    assignment.current_phase = AssignmentPhase.review
    
    from app.models.content import StatusLog
    log = StatusLog(
        campaign_id=assignment.campaign_id,
        actor_id=actor_id,
        from_status=AssignmentPhase.content_creation.value,
        to_status=AssignmentPhase.review.value,
        note="Influencer submitted draft content for review."
    )
    db.add(log)
    
    from app.models.notification import Notification, NotificationType
    notif = Notification(
        user_id=assignment.campaign.brand.user_id,
        title="Content Submitted",
        message=f"Influencer submitted draft content for '{assignment.campaign.title}'.",
        type=NotificationType.campaign_update
    )
    db.add(notif)
        
    await db.commit()
    await db.refresh(content)
    return content


async def get_assignment_contents(db: AsyncSession, assignment_id: int) -> list[SubmittedContent]:
    query = (
        select(SubmittedContent)
        .where(SubmittedContent.assignment_id == assignment_id)
        .order_by(SubmittedContent.submitted_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_content_by_id(db: AsyncSession, content_id: int) -> SubmittedContent | None:
    query = (
        select(SubmittedContent)
        .where(SubmittedContent.id == content_id)
        .options(
            selectinload(SubmittedContent.assignment)
            .selectinload(CampaignAssignment.campaign),
            selectinload(SubmittedContent.assignment)
            .selectinload(CampaignAssignment.influencer)
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


async def review_content(
    db: AsyncSession, content: SubmittedContent, review_data: ContentReviewRequest, actor_id: int
) -> SubmittedContent:
    if content.assignment.current_phase != AssignmentPhase.review:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=f"Cannot review content from {content.assignment.current_phase}")

    content.status = ContentStatus(review_data.decision)
    content.reviewed_at = datetime.now(timezone.utc)
    
    from app.models.content import StatusLog

    if review_data.decision == "approved":
        content.assignment.current_phase = AssignmentPhase.approved
        log = StatusLog(
            campaign_id=content.assignment.campaign_id,
            actor_id=actor_id,
            from_status=AssignmentPhase.review.value,
            to_status=AssignmentPhase.approved.value,
            note="Brand approved content."
        )
        db.add(log)
    elif review_data.decision == "changes_requested":
        content.assignment.current_phase = AssignmentPhase.content_creation
        log = StatusLog(
            campaign_id=content.assignment.campaign_id,
            actor_id=actor_id,
            from_status=AssignmentPhase.review.value,
            to_status=AssignmentPhase.content_creation.value,
            note="Brand requested changes to content."
        )
        db.add(log)
        
    # Create notification for the influencer
    campaign_title = content.assignment.campaign.title
    if review_data.decision == "approved":
        message = f"Your content for '{campaign_title}' was approved!"
    else:
        message = f"Changes were requested on your content for '{campaign_title}'."
        
    notification = Notification(
        user_id=content.assignment.influencer.user_id,
        title="Content Review",
        message=message,
        type=NotificationType.campaign_update
    )
    db.add(notification)
        
    await db.commit()
    await db.refresh(content)
    return content


async def add_content_comment(
    db: AsyncSession, content_id: int, author_id: int, text: str
) -> ContentComment:
    comment = ContentComment(
        content_id=content_id,
        author_id=author_id,
        comment=text
    )
    db.add(comment)
    await db.commit()
    
    # Safely load the relationship using a new query to avoid MissingGreenlet in async mode
    query = (
        select(ContentComment)
        .where(ContentComment.id == comment.id)
        .options(selectinload(ContentComment.author))
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_content_comments(db: AsyncSession, content_id: int) -> list[ContentComment]:
    query = (
        select(ContentComment)
        .where(ContentComment.content_id == content_id)
        .order_by(ContentComment.created_at.asc())
        .options(selectinload(ContentComment.author))
    )
    result = await db.execute(query)
    return list(result.scalars().all())
