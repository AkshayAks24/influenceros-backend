from sqlalchemy import case, func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from app.models.user import User
from app.models.notification import Notification, NotificationType

async def get_conversations_for_user(db: AsyncSession, user_id: int):
    # Determine the "other" user ID for each message
    other_user_col = case(
        (Message.sender_id == user_id, Message.receiver_id),
        else_=Message.sender_id
    ).label("other_user_id")

    # Explicit query grouping by the "other" user id to find the latest message
    subq = (
        select(
            other_user_col,
            func.max(Message.id).label("latest_message_id"),
            func.sum(
                case((and_(Message.receiver_id == user_id, Message.is_read == False), 1), else_=0)
            ).label("unread_count")
        )
        .where(or_(Message.sender_id == user_id, Message.receiver_id == user_id))
        .group_by("other_user_id")
        .subquery()
    )

    query = (
        select(
            subq.c.other_user_id,
            User.name.label("other_user_name"),
            Message.message.label("last_message"),
            Message.created_at.label("last_message_at"),
            subq.c.unread_count
        )
        .select_from(subq)
        .join(Message, Message.id == subq.c.latest_message_id)
        .join(User, User.id == subq.c.other_user_id)
        .order_by(Message.created_at.desc())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "other_user_id": row.other_user_id,
            "other_user_name": row.other_user_name,
            "last_message": row.last_message,
            "last_message_at": row.last_message_at,
            "unread_count": int(row.unread_count)
        }
        for row in rows
    ]

async def get_messages_between_users(db: AsyncSession, user_id: int, other_user_id: int):
    query = (
        select(Message)
        .where(
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
            )
        )
        .order_by(Message.created_at.asc())
    )
    result = await db.execute(query)
    messages = list(result.scalars().all())
    
    # Mark unread from other_user_id as read side-effect
    unread = [m for m in messages if m.receiver_id == user_id and not m.is_read]
    if unread:
        for m in unread:
            m.is_read = True
        await db.commit()
        
    return messages

async def create_message(db: AsyncSession, sender_id: int, data) -> Message:
    # We must use dynamic schema unpacking or manual assignment
    msg = Message(
        sender_id=sender_id,
        receiver_id=data.receiver_id,
        message=data.message
    )
    db.add(msg)
    
    # Send a notification to the receiver
    sender = await db.get(User, sender_id)
    sender_name = sender.name if sender else "Someone"
    notif = Notification(
        user_id=data.receiver_id,
        title="New Message",
        message=f"{sender_name} sent you a message",
        type=NotificationType.message
    )
    db.add(notif)
    
    await db.commit()
    await db.refresh(msg)
    return msg
