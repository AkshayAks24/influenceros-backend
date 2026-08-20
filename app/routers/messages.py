from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse, ConversationSummary
from app.services.message_service import (
    get_conversations_for_user,
    get_messages_between_users,
    create_message
)

router = APIRouter(tags=["Messages"])

@router.get(
    "/conversations",
    response_model=list[ConversationSummary],
    summary="Get user conversations",
    description="""
    Retrieves a list of all active conversations for the authenticated user, summarizing the latest message and unread counts.
    
    **Access Level:** Any authenticated user
    
    **Error Codes:** None specific to this endpoint.
    """
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_conversations_for_user(db, current_user.id)

@router.get(
    "/conversations/{other_user_id}/messages",
    response_model=list[MessageResponse],
    summary="Get conversation messages",
    description="""
    Retrieves the full message history between the authenticated user and another specified user.
    
    **Access Level:** Any authenticated user
    
    **Error Codes:** None specific to this endpoint.
    """
)
async def get_conversation_messages(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_messages_between_users(db, current_user.id, other_user_id)

@router.post(
    "/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    description="""
    Sends a direct message to another user.
    
    **Access Level:** Any authenticated user
    
    **Error Codes:**
    - `400 Bad Request`: The user attempted to send a message to themselves.
    - `404 Not Found`: The specified receiver user does not exist.
    """
)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if data.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
        
    # Validation to check if receiver actually exists could be added here
    # but the foreign key constraint will catch it (or we can add an explicit check to avoid 500)
    receiver = await db.get(User, data.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
        
    return await create_message(db, current_user.id, data)
