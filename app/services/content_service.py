from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content import SubmittedContent, ContentStatus, ContentComment
from app.models.application import CampaignAssignment, AssignmentPhase
from app.schemas.content import SubmittedContentCreate, ContentReviewRequest


async def get_assignment_by_id(db: AsyncSession, assignment_id: int) -> CampaignAssignment | None:
    query = (
        select(CampaignAssignment)
        .where(CampaignAssignment.id == assignment_id)
        .options(selectinload(CampaignAssignment.campaign))
    )
    result = await db.execute(query)
    return result.scalars().first()


async def submit_content(
    db: AsyncSession, assignment: CampaignAssignment, data: SubmittedContentCreate
) -> SubmittedContent:
    content = SubmittedContent(
        assignment_id=assignment.id,
        status=ContentStatus.pending_review,
        **data.model_dump()
    )
    db.add(content)
    
    if assignment.current_phase == AssignmentPhase.content_creation:
        assignment.current_phase = AssignmentPhase.review
        
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
            .selectinload(CampaignAssignment.campaign)
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


async def review_content(
    db: AsyncSession, content: SubmittedContent, review_data: ContentReviewRequest
) -> SubmittedContent:
    content.status = ContentStatus(review_data.decision)
    content.reviewed_at = datetime.now(timezone.utc)
    
    if review_data.decision == "approved":
        content.assignment.current_phase = AssignmentPhase.approved
        
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
    await db.refresh(comment, ["author"])
    return comment


async def get_content_comments(db: AsyncSession, content_id: int) -> list[ContentComment]:
    query = (
        select(ContentComment)
        .where(ContentComment.content_id == content_id)
        .order_by(ContentComment.created_at.asc())
        .options(selectinload(ContentComment.author))
    )
    result = await db.execute(query)
    return list(result.scalars().all())
